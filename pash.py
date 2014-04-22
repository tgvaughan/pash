from sys import argv, exit, stdin
from os import mkdir, path, ttyname, getcwd, listdir
from argparse import ArgumentParser
from ConfigParser import ConfigParser


def getConfigDir():
    return path.expanduser("~/.cwd_config")

def getCWDfileName():
    return path.join(getConfigDir(),"cwd" + ttyname(stdin.fileno()).replace("/","_"))

def getOtherCWDfileName(otherTTYname):
    return path.join(getConfigDir(),"cwd_dev_" + otherTTYname.replace("@","").replace("/","_"))

def getMainCWDfileName():
    return path.join(getConfigDir(),"main_cwd")

def getAliasFileName():
    return path.join(getConfigDir(),"aliases")

def getAliasConfigParser():
    configParser = ConfigParser()
    if path.exists(getAliasFileName()):
        configParser.read(getAliasFileName())
    return configParser

def storeCWD():
    for cwdfilename in [getCWDfileName(), getMainCWDfileName()]:
        with open(cwdfilename,'w') as cwdfile:
            cwdfile.write(path.abspath(getcwd()))
            cwdfile.close()
    
def getStoredCWD(otherTTYname=""):
    if otherTTYname=="":
        return open(getMainCWDfileName(),'r').readline()
    else:
        return open(getOtherCWDfileName(otherTTYname),'r').readline()

def getOtherTTYsWithCWDs():
    ttyStrings = []
    for fname in filter(lambda x: x.startswith("cwd"), listdir(getConfigDir())):
        if not path.abspath(path.join(getConfigDir(),fname))==getCWDfileName():
            ttyStrings.append("@" + fname.replace("cwd_dev_","").replace("_","/"))

    return ttyStrings

def getAliasList(omitPaths=False):
    aliasList=[]
    aliasParser = getAliasConfigParser()

    cwd = getStoredCWD()
    for dirname in aliasParser.sections():
        if cwd.startswith(dirname):
            for item in aliasParser.items(dirname):
                astr = "{}='{}'".format(item[0],item[1])
                if not omitPaths:
                    astr += " [{}]".format(dirname)
                aliasList.append(astr)

    return aliasList

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
        eval $a
    done
}}
    
function pash_cd () {{
    cd $@
    python {x} cd
    pash_load_aliases
}}
unalias cd 2>/dev/null
alias cd=pash_cd

function pash_cdc () {{
     todir=`python {x} cdc $1`
     cd $todir
}}
unalias cdc 2>/dev/null
alias cdc=pash_cdc

function pash_cdc_complete () {{
    i=1
    for tty in `python {x} listOtherTTYs "$2"`; do
        COMPREPLY[$i]=$tty
        let i=i+1
    done
}}
complete -F pash_cdc_complete cdc

alias la='python {x} aliasList'

function lan () {{
    python {x} aliasNew "$@"
    pash_load_aliases
}}

function lad () {{
    if [ $# -eq 1 ]; then
        python {x} aliasDel $1
        unalias $1
    fi
}}
""".format(x=argv[0])

def cmd_cd(args):
    storeCWD()

def cmd_cdc(args):
    print getStoredCWD(args.othertty)

def cmd_listOtherTTYs(args):
    for ttystr in getOtherTTYsWithCWDs():
        if ttystr.startswith(args.partial):
            print ttystr
    
def cmd_aliasList(args):
    for astr in getAliasList():
        print astr
        
def cmd_aliasLoad(args):
    for astr in getAliasList(True):
        print "alias " + astr
        
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

    parse_cd = subparsers.add_parser('cd', description="""
    Updating recorded CWD for this terminal following directory change.""")
    parse_cd.set_defaults(func=cmd_cd)

    parse_cdc = subparsers.add_parser('cdc', description="""
    Obtain CWD of any current terminal.""")
    parse_cdc.add_argument("othertty", default="", nargs="?")
    parse_cdc.set_defaults(func=cmd_cdc)

    parse_listOtherTTYs = subparsers.add_parser('listOtherTTYs', description="""
    Obtain list of _other_ TTYs with stored CWDs.""")
    parse_listOtherTTYs.add_argument("partial", type=str)
    parse_listOtherTTYs.set_defaults(func=cmd_listOtherTTYs)

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
    Load all applicable aliases.""")
    parse_aliasLoad.set_defaults(func=cmd_aliasLoad)

    if len(argv)==1:
        parser.print_usage()
        exit(0)

    # Initialize cwd file named after controlling tty
    if not path.exists(getConfigDir()):
        mkdir(getConfigDir())
    for CWDfileName in [getCWDfileName(), getMainCWDfileName()]:
        with open(CWDfileName,'w') as cwdfile:
            cwdfile.write(getcwd())
            cwdfile.close()
        
    args = parser.parse_args(argv[1:])
    args.func(args)
