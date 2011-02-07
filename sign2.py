from M2Crypto import BIO, Rand, SMIME
import subprocess
import json
class signerbox():
    def __init__(self):
        # Seed the PRNG.
        Rand.load_file('randpool.dat', -1)
        # Instantiate an SMIME object; set it up; sign the buffer.
        self.SMIME = SMIME.SMIME()
        #s.load_key('signer_key.pem', 'signer.pem')
    

    
    
    def load_private_key(self,pem_signer_key, pem_signer_cert):
    
        self.SMIME.load_key(pem_signer_key, pem_signer_cert)
        # Make a MemoryBuffer of the message.
        self.pem_signer_key = pem_signer_key
        self.pem_signer_cert = pem_signer_cert
    
    
    
        
    def signmsg(self,message):
        buf = BIO.MemoryBuffer(message)
        p7 = self.SMIME.sign(buf, SMIME.PKCS7_DETACHED)
        buf = BIO.MemoryBuffer(message)
        # Output p7 in mail-friendly format.
        out = BIO.MemoryBuffer()
        #out.write('From: sender@example.dom\n')
        #out.write('To: recipient@example.dom\n')
        #out.write('Subject: M2Crypto S/MIME testing\n')
        self.SMIME.write(out, p7, buf)
        output = str(out.read())
        # Save the PRNG's state.
        return output



    def test_sign(self,cleartext):
        buf = BIO.MemoryBuffer(self.cleartext)
        
        self.SMIMEload_key('tests/signer_key.pem', 'tests/signer.pem')
        p7 = self.SMIMEsign(buf)
        assert len(buf) == 0
        assert p7.type() == SMIME.PKCS7_SIGNED, p7.type()
        assert isinstance(p7, SMIME.PKCS7), p7
        out = BIO.MemoryBuffer()
        p7.write(out)
        
        buf = out.read()
        
        assert buf[:len('-----BEGIN PKCS7-----')] == '-----BEGIN PKCS7-----'
        buf = buf.strip()
        assert buf[-len('-----END PKCS7-----'):] == '-----END PKCS7-----', buf[-len('-----END PKCS7-----'):]
        assert len(buf) > len('-----END PKCS7-----') + len('-----BEGIN PKCS7-----')
        
        self.SMIMEwrite(out, p7, BIO.MemoryBuffer(self.cleartext))
        return out

    def test_store_load_info(self):        
        st = X509.X509_Store()
        self.assertRaises(X509.X509Error, st.load_info, 'tests/ca.pem-typoname')
        self.assertEqual(st.load_info('tests/ca.pem'), 1) 

    def test_verify_old(self,file_name):
        s = SMIME.SMIME()
        
        x509 = X509.load_cert('tests/signer.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        self.SMIME.set_x509_stack(sk)
        
        st = X509.X509_Store()
        st.load_info('tests/ca.pem')
        self.SMIME.set_x509_store(st)
        
        p7, data = SMIME.smime_load_pkcs7_bio(file_name)
        
        assert data.read() == self.cleartext
        assert isinstance(p7, SMIME.PKCS7), p7
        v = self.SMIME.verify(p7)
        assert v == self.cleartext
    
        t = p7.get0_signers(sk)
        assert len(t) == 1
        assert t[0].as_pem() == x509.as_pem(), t[0].as_text()


    def test_verify(self,data):
        cmd = "openssl smime -verify -CAfile gridka-ca.pem "
        openssl = subprocess.Popen(cmd,
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        )
        stdout_value, stderr_value = openssl.communicate(data)
        
        Verified = False
        verified_index = stderr_value.find('Verification successful',0,80)
        if verified_index == 0:
            Verified = True
        return Verified,stdout_value

    def test_verifyBad(self):
        s = SMIME.SMIME()
        
        x509 = X509.load_cert('tests/recipient.pem')
        sk = X509.X509_Stack()
        sk.push(x509)
        self.SMIME.set_x509_stack(sk)
        
        st = X509.X509_Store()
        st.load_info('tests/recipient.pem')
        self.SMIME.set_x509_store(st)
        
        p7, data = SMIME.smime_load_pkcs7_bio(self.signed)
        assert data.read() == self.cleartext
        assert isinstance(p7, SMIME.PKCS7), p7
        self.assertRaises(SMIME.PKCS7_Error, self.SMIME.verify, p7) # Bad signer


        
    def __del__ (self):
        Rand.save_file('randpool.dat')



if __name__ == "__main__":
    pem_signer_key = '/home/oms101/.globus/userkey.pem'
    pem_signer_cert = '/home/oms101/.globus/usercert.pem'
    box = signerbox()
    box.load_private_key(pem_signer_key, pem_signer_cert)
    out = box.signmsg('a sign of our times')
    
    data = ''
    for line in open('sign.p7'):
        data += line
    print data
    output = box.test_verify(data)
    print output
