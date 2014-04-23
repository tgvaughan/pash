from sys import argv, exit, stdin
from os import mkdir, path, ttyname, getcwd, listdir, remove
from argparse import ArgumentParser
from ConfigParser import ConfigParser


def getConfigDir():
    return path.abspath(path.expanduser("~/.cwd_config"))

def getTTYid():
    return ttyname(stdin.fileno()).replace("/","_")

### CWD management ###

def getCWDfileName():
    return path.abspath(path.join(getConfigDir(),"cwd" + getTTYid()))

def getMainCWDfileName():
    return path.abspath(path.join(getConfigDir(),"main_cwd"))

def storeCWD():
    with open(getCWDfileName(),'w') as cwdfile:
        cwdfile.write(path.abspath(getcwd()))
        cwdfile.close()

def storeMainCWD():
    with open(getMainCWDfileName(),'w') as cwdfile:
        cwdfile.write(path.abspath(getcwd()))
        cwdfile.close()            
            
def getStoredCWD():
    if not path.exists(getCWDfileName()):
        storeCWD()
    return open(getCWDfileName(),'r').readline()

def getStoredMainCWD():
    if not path.exists(getMainCWDfileName()):
        storeMainCWD()
    return open(getMainCWDfileName(),'r').readline()

def getOtherStoredCWDs():
    cwdStrings = []
    for fname in filter(lambda x: x.startswith("cwd"), listdir(getConfigDir())):
        thisCWDfileName = path.abspath(path.join(getConfigDir(), fname))
        if thisCWDfileName != getCWDfileName():
            cwdStrings.append(open(thisCWDfileName,'r').readline())

    return cwdStrings

def delOtherStoredCWDs():
    for fname in filter(lambda x: x.startswith("cwd"), listdir(getConfigDir())):
        thisCWDfileName = path.abspath(path.join(getConfigDir(), fname))
        if thisCWDfileName != getCWDfileName():
            remove(thisCWDfileName)
    

### Aliases ###

def getAliasFileName():
    return path.join(getConfigDir(),"aliases")

def getAliasConfigParser():
    configParser = ConfigParser()
    if path.exists(getAliasFileName()):
        configParser.read(getAliasFileName())
    return configParser

def getAliasList():
    aliasList=[]
    aliasParser = getAliasConfigParser()

    cwd = getStoredCWD()
    for dirname in aliasParser.sections():
        if cwd.startswith(dirname):
            for item in aliasParser.items(dirname):
                aliasList.append((item[0],item[1],dirname))

    return aliasList

def getLoadedAliasesFileName():
    return path.abspath(path.join(getConfigDir(),"aliases" + getTTYid()))

def getLoadedAliases():
    aliasList = []
    if path.exists(getLoadedAliasesFileName()):
        with open(getLoadedAliasesFileName(),'r') as fob:
            for line in fob.readlines():
                aliasList.append(line.strip())
    return aliasList

def storeLoadedAliases(aliasList):
    with open(getLoadedAliasesFileName(),'w') as fob:
        for alias in aliasList:
            fob.write(alias[0] + "\n")

def addAlias(name, value):
    aliasParser = getAliasConfigParser()
    
    cwd = getStoredCWD()
    if not aliasParser.has_section(cwd):
        aliasParser.add_section(cwd)
        
    aliasParser.set(cwd, name, value)
    aliasParser.write(open(getAliasFileName(),'w'))

def delAlias(name):
    aliasParser = getAliasConfigParser()

    cwd = getStoredCWD()
    if not aliasParser.has_section(cwd):
        print "No aliases set for the current directory."
        return

    if not aliasParser.has_option(cwd, name):
        print "No such alias for the current directory."
        return

    aliasParser.remove_option(cwd, name)
    if len(aliasParser.items(cwd))==0:
        aliasParser.remove_section(cwd)

    aliasParser.write(open(getAliasFileName(),'w'))


### Commands ###

def cmd_init(args):
    """Generate commands to initialize bash."""

    print """
function pash_load_aliases () {{
    IFS=$'\n'
    for a in `python {x} aliasLoad`; do
        eval $a 2>/dev/null
    done
}}
    
function pash_cd () {{
    cd $@
    python {x} storeCWD
    pash_load_aliases
}}
unalias cd 2>/dev/null
alias cd=pash_cd

function cdc () {{
    if [ $# -gt 0 ]; then
        cd $@
    else
        cd `python {x} getMainCWD`
    fi
}}

function _cdc_complete () {{
    i=1
    for tty in `python {x} listOtherCWDs "$2"`; do
        COMPREPLY[$i]=$tty
        let i=i+1
    done
}}
complete -F _cdc_complete cdc

function cdd () {{
    python {x} delOtherCWDs
}}

alias la='python {x} aliasList'

function lan () {{
    python {x} aliasNew "$@"
    pash_load_aliases
}}

function lad () {{
    if [ $# -eq 1 ]; then
        python {x} aliasDel $1
        pash_load_aliases
    fi
}}
""".format(x=argv[0])

def cmd_storeCWD(args):
    storeCWD()
    storeMainCWD()

def cmd_getMainCWD(args):
    print getStoredMainCWD()
    
def cmd_listOtherCWDs(args):
    for cwd in getOtherStoredCWDs():
        if cwd.startswith(args.partial):
            print cwd

def cmd_delOtherCWDs(args):
    delOtherStoredCWDs()
            
def cmd_aliasList(args):
    for alias in getAliasList():
        print "{}='{}' [{}]".format(alias[0], alias[1], alias[2])
        
def cmd_aliasLoad(args):
    for astr in getLoadedAliases():
        print  "unalias " + astr

    aliasList = getAliasList()
    
    for alias in aliasList:
        print "alias {}='{}'".format(alias[0], alias[1])

    storeLoadedAliases(aliasList)
        
def cmd_aliasNew(args):
    addAlias(args.name, args.value)

def cmd_aliasDel(args):
    delAlias(args.name)


### MAIN ###
    
if __name__=='__main__':

    parser = ArgumentParser(description="Python Shell Tool")

    subparsers = parser.add_subparsers(title='Valid Commands', description="""
    Use '{} cmd -h' to get help on cmd.""".format(argv[0]))

    parse_init = subparsers.add_parser('init', description="""
    Generate (bash) shell commands for initialization.""")
    parse_init.set_defaults(func=cmd_init)

    parse_cd = subparsers.add_parser('storeCWD', description="""
    Updating recorded CWD for this terminal following directory change.""")
    parse_cd.set_defaults(func=cmd_storeCWD)

    parse_getMainCWD = subparsers.add_parser('getMainCWD', description="""
    Get main (shared) CWD.""")
    parse_getMainCWD.set_defaults(func=cmd_getMainCWD)
        
    parse_listOtherCWDs = subparsers.add_parser('listOtherCWDs', description="""
    Obtain list of _other_ stored CWDs.""")
    parse_listOtherCWDs.add_argument("partial", type=str)
    parse_listOtherCWDs.set_defaults(func=cmd_listOtherCWDs)

    parse_delOtherCWDs = subparsers.add_parser('delOtherCWDs', description="""
    Delete all other stored CWDs.""")
    parse_delOtherCWDs.set_defaults(func=cmd_delOtherCWDs)

    parse_aliasNew = subparsers.add_parser('aliasNew', description="""
    Create new local alias.""")
    parse_aliasNew.add_argument("name", type=str, help="Alias name")
    parse_aliasNew.add_argument("value", type=str, help="Alias value")
    parse_aliasNew.set_defaults(func=cmd_aliasNew)

    parse_aliasDel = subparsers.add_parser('aliasDel', description="""
    Create new local alias.""")
    parse_aliasDel.add_argument("name", type=str, help="Alias name")
    parse_aliasDel.set_defaults(func=cmd_aliasDel)

    parse_aliasList = subparsers.add_parser('aliasList', description="""
    List all applicable aliases.""")
    parse_aliasList.set_defaults(func=cmd_aliasList)

    parse_aliasLoad = subparsers.add_parser('aliasLoad', description="""
    Generate bash commands for loading all applicable aliases.""")
    parse_aliasLoad.set_defaults(func=cmd_aliasLoad)

    if len(argv)==1:
        parser.print_usage()
        exit(0)

    # Initialize cwd file named after controlling tty
    if not path.exists(getConfigDir()):
        mkdir(getConfigDir())
        
    args = parser.parse_args(argv[1:])
    args.func(args)
