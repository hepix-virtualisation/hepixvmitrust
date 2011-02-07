import json_encoder

import optparse
import os
import sys
import hashlib
import os.path

interestingkeys = ['md5sum','updatemetadata','votag','vo','updatemetadata',
    'architecture','platform','kernel','uuid','image_file','pem_signer_cert',
    'pem_signer_key','pem_signer_key']

def parse_env():
    output = {}
    for param in os.environ.keys():
        output[param] = os.environ[param]
    return output

def hasher(md5sum_file):
    if md5sum_file == None:
        return
    if not os.path.isfile(md5sum_file):
        return None
    m = hashlib.sha512()
    for line in md5sum_file:
        m.update(line)
    return m.hexdigest()
    
def get_keys_from_env():
    """ Read settign sfrom the enviroment
    $export VMIC_TOOLS_votag=atlas
    """
    
    enviroment = parse_env()
    enviromentkeyset = set(enviroment.keys())
    mappingkeys = {}
    myset = set()
    veryintersting = {}
    for tmp in interestingkeys:
        interestingkeys_item = str("VMIC_TOOLS_%s" % (tmp))
        veryintersting[interestingkeys_item] = str(tmp)
        #print interestingkeys_item
    #availablekeys = set(veryintersting.keys())
    #print "availablekeys=%s" %(availablekeys)
    
    #print veryintersting
    #print enviromentkeyset
    
    veryinterestingkeys = set(veryintersting.keys()) 
    #print veryinterestingkeys
    output = {}
    set_of_found = set(veryintersting.keys()) & enviromentkeyset
    for key in set_of_found:
        #print ("key=%s" % (key))
        #print ("veryintersting[key]=%s" % (veryintersting[key]))
        output[veryintersting[key]] = enviroment[key]
    #print "output=%s" % output
    return output

def cleaninputfile(filename):
    strname = str(filename)
    return strname.strip("'")
class jobmanger:
    def __init__(self):
        self.keys = {}
        self.msg_chain = json_encoder.json_chain()
        self.get_keys_from_env()
        
    def get_keys_from_env(self):
        """ Read settign sfrom the enviroment
        $export VMIC_TOOLS_votag=atlas
        """

        enviroment = parse_env()
        enviromentkeyset = set(enviroment.keys())
        mappingkeys = {}
        myset = set()
        veryintersting = {}
        for tmp in interestingkeys:
            interestingkeys_item = str("VMIC_TOOLS_%s" % (tmp))
            veryintersting[interestingkeys_item] = str(tmp)
            #print interestingkeys_item
        availablekeys = set(veryintersting.keys())
        #print "availablekeys=%s" %(availablekeys)

        #print veryintersting
        #print enviromentkeyset

        veryinterestingkeys = set(veryintersting.keys()) 
        #print veryinterestingkeys
        output = {}
        set_of_found = set(veryintersting.keys()) & enviromentkeyset
        for key in set_of_found:
            #print ("key=%s" % (key))
            #print ("veryintersting[key]=%s" % (veryintersting[key]))
            output[veryintersting[key]] = enviroment[key]
        #print "output=%s" % output
        return output        
    def loadkeys(self,keys):
        #print "keys=%s" %(keys)
        setofcurrentkeys = set(self.keys.keys())
        #print "setofcurrentkeys=%s" %(setofcurrentkeys)
        setofnewkeys = set(keys.keys())
        #print "setofnewkeys=%s" %(setofnewkeys)
        setofnewnewkeys = setofnewkeys - setofcurrentkeys
        #print "setofnewnewkeys=%s" %(setofnewnewkeys)
        
        for key in setofnewkeys:
            #print "loadkeys.key=%s" % (key)
            #print "self.keys[key] = keys[key] %s - " %  (self.keys.keys())
            #print "self.keys[key] = keys[key] %s - %s" %  (self.keys[key] , keys[key])
            self.keys[key] = keys[key]
        #output = self.msg_chain.load_keys(self.keys['pem_signer_key'],self.keys['pem_signer_cert'])
   

    def getfilesystempointer(outputfile):
        if outputfile == None:
            return sys.stdin
        return open(outputfile,'r')

    def validateoptions(options,tasks_wanted):
        for item in taskwanted.keys():
            options = taskwanted[item].getrequired_options()
        return tasks_allowed,tasks_prevented

    def setupsign(self):
        required = set(['pem_signer_key','pem_signer_cert'])
        bill = set(self.keys.keys())
        if not required.issubset(self.keys.keys()):
            print "required.issubset(self.keys.keys())=%s" % (required.issubset(self.keys.keys()))
            print "missingfiles must exit=%s" % (required)
            return False
        #print "missingfile333s=%s" % (self.keys['pem_signer_key'])
        #print self.keys()
        
        self.loaded_keys = self.msg_chain.load_keys(self.keys['pem_signer_key'],self.keys['pem_signer_cert'])
        return True
        #print output
    def hashfiles(self, filelist):
        output = []
        for filename in filelist:
            
            
            sha512 = hasher(filename)
            #print "sha512 = %s " % (sha512)
            output.append({
                'filename':repr(filename),
                'digest:sha512':repr(hasher(filename)),
            })
            
            #content = 
        
        self.keys['vmic'] = output
    def signfile(self):
        
        
        
        
        

        messagesss = self.msg_chain.make_message([self.keys])
        #print self.keys
        self.msg_chain.setserialisejson(messagesss)
        #print self.keys
        self.msg_chain.encode()
        #print self.keys
        return self.msg_chain.message_signed
    def makemetdata(self):
        
        pass

def main():
    """Runs program and handles command line options"""
    keys = {}
    
    p = optparse.OptionParser()
    p.add_option('-f', '--image_file', action ='append', help='Make meta data for this image')
    p.add_option('-s', '--sign', action ='store', help='returns verbose output')
    p.add_option('-v', '--verbose', action ='store_true', help='returns verbose output')
    p.add_option('-i', '--stdin', action ='store_true', help='signs input on stdin')
    p.add_option('-e', '--envorment', action ='store', help='Enviroment_list')
    p.add_option('-k', '--signer_key', action ='store', help='path to signer key')
    p.add_option('-c', '--signer_certificate', action ='store', help='path to signer certificate')
    
    options, arguments = p.parse_args()
    filelist = []
    
    if len(options.image_file) == 0:
        print "No files specified"
        return 0
    else:
        files = []
        for line in options.image_file:
            filelist.append(cleaninputfile(line))
    
    if options.sign:
        keys['signfile'] = cleaninputfile(options.sign())
        print "f%sf" % (keys['signfile'])
    
    
    if options.signer_key:
        key_cleaned = cleaninputfile(options.signer_key)
        #print "===%s===" % (key_cleaned)
        keys['pem_signer_key'] = key_cleaned
        #print "f%sfdfff" % (keys['pem_signer_key'])
    if options.signer_certificate:
        cert_cleaned = cleaninputfile(options.signer_certificate)
        #print "===%s===" % (cert_cleaned)
        keys['pem_signer_cert'] = cert_cleaned
        #print "dfsdfSDF"
        #print "f%sf" % (keys['pem_signer_cert'])
        #pass
    #keys['pem_signer_key'] = "/home/oms101/.globus/userkey.pem"
    #keys['pem_signer_cert'] = "/home/oms101/.globus/usercert.pem"
    #print "f%s---fdjjjj" % (keys['pem_signer_key'])
    jobstodo = jobmanger()
    jobstodo.loadkeys(keys)
    
    messagesss = jobstodo.makemetdata()
    
    jobstodo.hashfiles(filelist)
    
    
    
    
    #jobstodo.loadkeys(keys)
    if False == jobstodo.setupsign():
        print "error signing the keys"
        exit(1)
    signedfile = jobstodo.signfile()
    print signedfile

if __name__ == "__main__":
    main()
