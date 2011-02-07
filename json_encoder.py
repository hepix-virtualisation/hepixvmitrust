import json
import sign2
from M2Crypto import BIO, Rand, SMIME



    

class json_chain:
    def __init__(self):
        self.pem_signer_key = None
        self.pem_signer_cert = None
        self.ver_architecture = 0
        self.ver_major = 0
        self.ver_minor = 1
        self.ver_patch = 0
        self.message_signed = None
        self.message_serialisable = []
        self.message_serialised = ""
        Rand.load_file('randpool.dat', -1)
        self.SMIME = SMIME.SMIME()
    

    def load_keys(self,pem_signer_key,pem_signer_cert):
        self.pem_signer_key = pem_signer_key
        self.pem_signer_cert = pem_signer_cert
        # Seed the PRNG.
        
        # Instantiate an SMIME object; set it up; sign the buffer.
        
        self.SMIME.load_key(self.pem_signer_key,self.pem_signer_cert)
    
    
    
    def setserialisejson(self,data):        
        serialisedtmp = json.dumps(data,
                skipkeys=False, 
                ensure_ascii=False,
                )
        if serialisedtmp == None:
            print "ops"
            return
        self.message_serialisable = data
        self.message_serialised = serialisedtmp
        return self.message_serialised 
        
    def encode(self,message = None):
        if not message:
            message = self.message_serialised
        buf = BIO.MemoryBuffer(message)
        
        p7 = self.SMIME.sign(buf, SMIME.PKCS7_DETACHED)
        buf = BIO.MemoryBuffer(message)
        # Output p7 in mail-friendly format.
        out = BIO.MemoryBuffer()
        #out.write('From: sender@example.dom\n')
        #out.write('To: recipient@example.dom\n')
        #out.write('Subject: M2Crypto S/MIME testing\n')
        self.SMIME.write(out, p7, buf)
        self.message_signed = str(out.read())
        return self.message_signed 
        # Save the PRNG's state.
        
        
        #result = self.SMIME.load_key(pem_signer_key, pem_signer_cert)
        
    def readmessages(self):
        output = []
        if hasattr(self,'message_signed'):
            output.append( "self.message_signed='%s'\n" % (self.message_signed))
        if hasattr(self,'message_serialisable'):
            output.append( "self.message_serialisable='%s'\n" % (self.message_serialisable))
        if hasattr(self,'message_serialised'):
            output.append( "self.message_serialised='%s'\n" % (self.message_serialised))
        return output
    def __del__ (self):
        Rand.save_file('randpool.dat')


    def make_message(self,input_message):
        messagelen = len(input_message)
        header = {'org.desy.grid.messaging.json_encoder' : {'ver' : [0,0,1,0],'imp' : [0,0,0,0]},
            'org.desy.grid.messaging.json_encoder.vmic' : {'ver' : [0,0,1,0],'imp' : [0,0,0,0]}}
        output = []
        output.append(header)
        for index in range(len(input_message)):
            output.append(input_message[index])
        return output
    


if __name__ == "__main__":
    msg_chain = json_chain()
    
    
    #box.load_private_key(pem_signer_key, pem_signer_cert)

    
    #pem_signer_key  = '/home/oms101/.globus/userkey.pem'
    #pem_signer_cert = '/home/oms101/.globus/usercert.pem'
    
    #debugging tool
    #mesages = msg_chain.readmessages()
    
    msg_chain.load_keys(str(pem_signer_key),str(pem_signer_cert))
    
    #debugging tool
    #mesages = msg_chain.readmessages()
   
    #print out
    input_message = []
    messagesss = msg_chain.make_message(input_message)
    msg_chain.setserialisejson(messagesss)
    msg_chain.encode()
    
    for line in msg_chain.message_signed.split('\n'):
        print line
