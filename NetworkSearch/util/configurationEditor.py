from ConfigParser import SafeConfigParser
import sys
import argparse

def get_args():
    current_path = sys.path[0]
    parser = argparse.ArgumentParser(description = "Configuration file editor (for a batch configuring)")
    parser.add_argument('-path', type=str, default=current_path[:current_path.rfind('/')]+'/config.cfg',
                        help='path to the configuration')
    parser.add_argument('-section', type=str, default='Node_Manager', 
                        help='section of the configuration (default="Node_Manager")')
    parser.add_argument('-option', type=str, default='neighbor_host', 
                        help='option of the configuration  (default="neighbor_host")')
    parser.add_argument('value', type=str, default='', help='value')    
    return parser.parse_args()

def main():
    # Read command arguments
    try:
        args = get_args()
    except IOError as (errno, strerror):
        print "IOError({0}): {1}".format(errno,strerror)

    configparser = SafeConfigParser()
    configparser.read([args.path])
    
    configparser.set(args.section,args.option,args.value)
    #write to a file
    with open(args.path, 'w') as fp:
        configparser.write(fp)
        
if __name__ == '__main__':
    exit(main())
    