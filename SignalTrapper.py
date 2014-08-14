class SignalTrapper:
    def __init__(self):
        self.STOP = False
        self.logger = logging.getLogger("Signal Trapper")
        self.logger.debug('STOP set to False')

    def trap(self):
        """Signal Trapper"""
        sig={}
        self.logger.debug('Starting Signal Trapper')
        for i in [x for x in dir(signal) if x.startswith("SIG")]:
            try:
                signum = getattr(signal,i)
                self.logger.debug('Trapping signal %s - %s ' %(i,signum))
#                print i,signum
                sig[signum] = i
                signal.signal(signum,self.handleSigTERM)
            except RuntimeError,m:
                self.logger.debug('Skipping %s - %s' % (i,m))
                pass
#                print "Skipping %s - %s" % (i,m)
            except ValueError,v:
                self.logger.debug('ValueError %s - %s' %(i,v))
                pass
#                print "ValueError %s - %s" %(i,v)

    def handleSigTERM(self,*arg, **kw):
        """Signal Handler"""
        self.logger.debug('Signal Handler')

        self.logger.debug('Signal %s received' % arg[0])

#        print 'Signal %s received' % arg[0]
        sys.stdout.flush()
        if arg[0] in [1,2,3,4,15,30]:
            sys.stdout.flush()
            self.logger.debug('STOP set to True')
            self.STOP = True

    def get_STOP(self):
#        logging.debug('Returning self.STOP with %s' % self.STOP)
        return self.STOP
