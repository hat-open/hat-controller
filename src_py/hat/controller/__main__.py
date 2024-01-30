import sys

from hat.controller.main import main


if __name__ == '__main__':
    sys.argv[0] = 'hat-controller'
    sys.exit(main())
