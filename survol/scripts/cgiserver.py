#!/usr/bin/python

YappiProfile = False
try:
    import yappi
except ImportError:
    YappiProfile = False

import sys
import getopt
import os
import socket

try:
	from urlparse import urlparse
except ImportError:
	from urllib.parse import urlparse

# If Apache is not available or if we want to run the website
# with a specific user account.

# In Apache httpd.conf, we have the directive:
# SetEnv PYTHONPATH C:\Users\rchateau\Developpement\ReverseEngineeringApps\PythonStyle\htbin\revlib
# It is also possible to set it globally in the .profile
# if not we get the error, for example:  import lib_pefile.
# sys.path.append('survol/revlib')

def ServerForever(server):
    if YappiProfile:
        try:
            yappi.start()
            server.serve_forever()
        except KeyboardInterrupt:
            print("Leaving")
            yappi.get_func_stats().print_all()
            yappi.get_thread_stats().print_all()
    else:
        server.serve_forever()

# Different specific cases:
# * In development mode, one process serves the HTML files of the UI and the Python files of the Agent,
#   all of them stored in the same directory. No cross-site scripting needed.
# * When deployed, acts as an Agent by running CGI scripts from lib-packages Python installed modules.
# * When deployed, acts as an Agent by running the single Python CGI script which imports installed modules.
# * When deployed, acts as a UI by running the HTML pages from the installation directory,
#   or from the directory defined by distutils or pkg_resources.

def Usage(progNam):
    print("Survol HTTP server: %s"%progNam)
    print("    -a,--address=<IP address> TCP/IP address")
    print("    -p,--port=<number>        TCP/IP port number")
    # Ex: -b "C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
    print("    -b,--browser=<program>    Starts a browser")
    print("    -v,--verbose              Verbose mode")

# Setup creates a binary script which directly calls this function.
# This changes the current directory, so that URLs can point to plain Python scripts.
# This can be avoided if we have an unique CGI script loading Python scripts as modules.
def RunCgiServer():
    # sys.path=['C:\\Users\\rchateau\\Developpement\\ReverseEngineeringApps\\PythonStyle\\testarea\\Scripts\\survol_cgiserver.exe', 'C:\\w
    # indows\\system32\\python27.zip', 'c:\\users\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea\\DLLs', 'c:\\use
    # rs\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea\\lib', 'c:\\users\\rchateau\\developpement\\reverseengine
    # eringapps\\pythonstyle\\testarea\\lib\\plat-win', 'c:\\users\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea
    # \\lib\\lib-tk', 'c:\\users\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea\\scripts', 'c:\\python27\\Lib', '
    # c:\\python27\\DLLs', 'c:\\python27\\Lib\\lib-tk', 'c:\\users\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea
    # ', 'c:\\users\\rchateau\\developpement\\reverseengineeringapps\\pythonstyle\\testarea\\lib\\site-packages']

    # curPth = r"C:\Users\rchateau\Developpement\ReverseEngineeringApps\PythonStyle\testarea\Lib\site-packages"
    curPth = None
    print("Searching internal packages")
    for pth in sys.path:
        if pth.endswith("site-packages"):
            curPth = pth
            break

    if curPth:
        print("Setting current path to %s"%curPth)
        os.chdir(curPth)
        RunCgiServerInternal()
    else:
        print("No python path to set")

# https://docs.python.org/2/library/webbrowser.html
def StartsWebrowser(browser_name,theUrl):
    """This starts a browser with the specific module to do it"""

    import webbrowser

    # TODO: Parses the argument from the parameter
    webbrowser.open(theUrl, new=0, autoraise=True)

def StartsBrowser(browser_name,theUrl):
    """This starts a browser whose executable is given on the command line"""
    # Import only if needed.
    import threading
    import time
    import subprocess

    def StartBrowserProcess():

        print("About to start browser: %s %s"%(browser_name,theUrl))

        # Leaves a bit of time so the HTTP server can start.
        time.sleep(5)

        subprocess.check_call([browser_name, theUrl])

    threading.Thread(target=StartBrowserProcess).start()
    print("Browser thread started")

# It is also possible to call the script from command line.
def RunCgiServerInternal():

    envPYTHONPATH = "PYTHONPATH"
    if 'win' in sys.platform:
        # This is necessary for revlib which is otherwise not found.
        extraPath = "survol"
        try:
            os.environ[envPYTHONPATH] = os.environ[envPYTHONPATH] + ";" + extraPath
        except KeyError:
            os.environ[envPYTHONPATH] =extraPath
        os.environ.copy()

    # This also works on Windows and Python 3.
    if 'linux' in sys.platform:
        sys.path.append("survol")

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:p:b:v", ["help","address=","port=","browser=","verbose"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        Usage()
        sys.exit(2)

    # It must be the same address whether it is local or guessed from another machine.
    # Equivalent to os.environ['SERVER_NAME']
    # server_addr = "rchateau-HP"
    # server_addr = "DESKTOP-NI99V8E"
    # It is possible to force this address to "localhost" or "127.0.0.1" for example.
    server_addr = socket.gethostname()

    verbose = False
    port_number = 8000
    browser_name = None

    for anOpt, aVal in opts:
        if anOpt == ("-v", "--verbose"):
            verbose = True
        elif anOpt in ("-a", "--address"):
            server_addr = aVal
        elif anOpt in ("-p", "--port"):
            port_number = int(aVal)
        elif anOpt in ("-b", "--browser"):
            browser_name = aVal
        elif anOpt in ("-h", "--help"):
            Usage(sys.argv[0])
            sys.exit()
        else:
            assert False, "Unhandled option"

    currDir = os.getcwd()
    print("cwd=%s path=%s"% (currDir, str(sys.path)))
    print("Opening %s:%d" % (server_addr,port_number))
    print("sys.path=%s"% str(sys.path))
    try:
        print("os.environ['%s']=%s"% (envPYTHONPATH,os.environ[envPYTHONPATH]))
    except KeyError:
        print("os.environ['%s']=%s"% (envPYTHONPATH,"Not defined"))

    # Starts a thread which will starts the browser.
    if browser_name:

        theUrl = "http://" + server_addr
        if port_number:
            if port_number != 80:
                theUrl += ":%d" % port_number
        theUrl += "/survol/www/index.htm"

        if browser_name.startswith("webbrowser"):
            StartsWebrowser(browser_name,theUrl)
        else:
            StartsBrowser(browser_name,theUrl)
        print("Browser thread started to:"+theUrl)

    # https://stackoverflow.com/questions/32241082/python-access-control-allow-origin
    # CORS Cross-site scripting must be activated.

    # Apache sets these environment variables.
    # SERVER_SOFTWARE=Apache/2.4.12 (Win64) OpenSSL/1.0.1m mod_wsgi/4.4.12 Python/2.7.10
    # SERVER_NAME=rchateau-hp
    # SERVER_ADDR=fe80::3c7a:339:64f0:2161
    # HTTP_HOST=rchateau-hp

    if sys.version_info[0] < 3:
        import CGIHTTPServer
        import BaseHTTPServer
        from BaseHTTPServer import HTTPServer
        from CGIHTTPServer import _url_collapse_path
        class MyCGIHTTPServer(CGIHTTPServer.CGIHTTPRequestHandler):
            def is_cgi(self):
                # self.path = "/survol/entity.py?xid=odbc/table.Dsn=DSN~MyNativeSqlServerDataSrc,Table=VIEWS"
                collapsed_path = _url_collapse_path(self.path)
                # print("is_cgi collapsed_path=%s"%collapsed_path)

                uprs = urlparse(collapsed_path)
                pathOnly = uprs.path
                # print("is_cgi pathOnly=%s"%pathOnly)

                fileName, fileExtension = os.path.splitext(pathOnly)

                # print("is_cgi pathOnly=%s fileExtension=%s"%(pathOnly,fileExtension))

                urlPrefix = "/survol/"
                if fileExtension == ".py" and pathOnly.startswith(urlPrefix):
                    dir_sep_index = len(urlPrefix)-1
                    head, tail = collapsed_path[:dir_sep_index], collapsed_path[dir_sep_index + 1:]
                    # print("is_cgi YES head=%s tail=%s"%(head, tail))
                    self.cgi_info = head, tail
                    return True
                else:
                    # print("is_cgi NOT")
                    return False

        server = BaseHTTPServer.HTTPServer
        handler = MyCGIHTTPServer

        server = HTTPServer((server_addr, port_number), handler)

        ServerForever(server)

    else:
        from http.server import CGIHTTPRequestHandler, HTTPServer
        class MyCGIHTTPServer(CGIHTTPRequestHandler):
            def is_cgi(self):
                sys.stdout.write("is_cgi self.path=%s\n" % self.path)

                # By defaut, self.cgi_directories=['/cgi-bin', '/htbin']
                sys.stdout.write("self.cgi_directories=%s\n" % self.cgi_directories)

                # https://stackoverflow.com/questions/17618084/python-cgihttpserver-default-directories
                self.cgi_info = '', self.path[1:]
                # So it always work.
                uprs = urlparse(self.path)
                pathOnly = uprs.path
                # print("is_cgi pathOnly=%s"%pathOnly)

                fileName, fileExtension = os.path.splitext(pathOnly)
                return fileExtension == ".py"



        handler = MyCGIHTTPServer
        server = HTTPServer((server_addr, port_number), handler)
        server.serve_forever()

if __name__ == '__main__':
    # If this is called from the command line, we are in test mode and must use the local Python code,
    # and not use the installed packages.
    # Here are the directories:
    # www/index.htm
    # www/js/base64.js
    #
    # In this mode, we assume that the Python scripts are here, on the same server.
    # survol/entity.py
    RunCgiServerInternal()
