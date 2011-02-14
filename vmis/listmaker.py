#!/usr/bin/env python
try:
    import json
except ImportError:
    import simplejson as json 
import codecs

import optparse
import os
import sys
import hashlib
import os.path
from M2Crypto import BIO, Rand, SMIME

class imagemodel:
    interestingkeys = set([u'vmi_uid'])
    def __init__(self,
        vmi_uid=None,
        vmi_url=None,
        vmi_hash_sha512=None,
        vmi_hypervisor=None,
        vmi_description=None,
        vmi_os_version=None,
        vmi_os_architecture=None,
        vmi_disk_size=None,
        ):
        
        self.metadata = {'vmi_uid' : vmi_uid,
            'vmi_url' : vmi_url,
            'vmi_hash_sha512' :vmi_hash_sha512,
            'vmi_url' : vmi_url,
            'vmi_hypervisor' : vmi_hypervisor,
            'vmi_description' : vmi_description,
            'vmi_os_version' : vmi_os_version,
            'vmi_os_architecture' : vmi_os_architecture,
            'vmi_disk_size' : vmi_disk_size}


class listmodel:
    interestingkeys = set([u'vmi_uid'])
    def __init__(self,owner_real_name=None,
        owner_email=None,
        vmi_url=None,
        vmic_url=None,
        images=[]):
        self.metadata = {
            'owner_real_name' : owner_real_name,
            'owner_email' : owner_email,
            'vmic_url' : vmic_url,
            'vmi_url' : vmi_url}
        self.images = images

class VMimageListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, imagemodel):
            return {'metadata' : obj.metadata}
        if isinstance(obj, listmodel):
            imagelist = []
            for i in obj.images:
                imagelist.append(self.default(i))
            return {'metadata' : obj.metadata, 'images' : imagelist}
        return json.JSONEncoder.default(self, obj)

def VMimageDecoder(dct):
    if u'metadata' in dct.keys():
        output =None
        metadata = dct[u'metadata']
        requiredmetadata = [u'vmi_uid',
            u'vmi_url',
            u'vmi_hash_sha512',
            u'vmi_hypervisor',
            u'vmi_description',
            u'vmi_os_version',
            u'vmi_os_architecture',
            u'vmi_disk_size']
        requiredmetadataset = set(requiredmetadata)
        if requiredmetadataset.issubset(metadata.keys()):
            output = imagemodel(vmi_uid=metadata[u'vmi_uid'],
                vmi_url=metadata[u'vmi_url'],
                vmi_hash_sha512=metadata[u'vmi_hash_sha512'],
                vmi_hypervisor=metadata[u'vmi_hypervisor'],
                vmi_description=metadata[u'vmi_description'],
                vmi_os_version=metadata[u'vmi_os_version'],
                vmi_os_architecture=metadata[u'vmi_os_architecture'],
                vmi_disk_size=metadata[u'vmi_disk_size']
                )
            return output
        return output
    return dct


class vmlistview:
    def load_file(self,filename):
        #print "filename=%s" % (filename)
        loadedfile = None
        with open(filename, 'r') as fp:
            loadedfile = json.load(fp)
            requiredkeys = [u'metadata', u'images']
            requiredkeysset = set(requiredkeys)
            if not requiredkeysset.issubset(loadedfile.keys()):
                return False
            listmetadata = loadedfile[u'metadata']
            requiredmetadata = [u'owner_real_name',
                u'owner_real_name',
                u'owner_email',
                u'vmic_url']
            requiredmetadataset = set(requiredmetadata)
            if not requiredmetadataset.issubset(listmetadata.keys()):
                return False
            images = loadedfile[u'images']
            allimages = []
            for image in images:
                translatedimage = VMimageDecoder(image)
                allimages.append(translatedimage)
            output = listmodel(owner_real_name=listmetadata[u'owner_real_name'],
                owner_email=listmetadata[u'owner_email'],
                vmic_url=listmetadata[u'vmic_url'],
                )
            output.images = allimages
            return output

        return False
    def save_file(self,entry,filename):
        with open(filename, 'w') as f:
            json.dump(entry, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
        return True
    def images_list(self,entry):
        #print "frod=%s" % (entry)
        for item in entry.images:
            print item.metadata[u'vmi_uid']
    def images_list(self,entry):
        #print "frod=%s" % (entry)
        for item in entry.images:
            print item.metadata[u'vmi_uid']
    def dumps(self,entry):
        return json.dumps(entry, cls=VMimageListEncoder, sort_keys=True, indent=4)

class vmlistcontroler:
    def __init__(self):
        self.view = vmlistview()
        self.model = listmodel()
    def load(self,filename):
        try:
            candidate = self.view.load_file(filename)
        except ValueError:
            return False
        if candidate == False:
            return False
        self.model = candidate
        return True
        
    def save(self,filename):
        self.view.save_file(self.model,filename)
        
    def images_list(self):
        if self.model == None:
            return False
        return self.view.images_list(self.model)
    def image_add(self,filename):
        with open(filename, 'r') as f:
            fred = json.load(f,object_hook=VMimageDecoder)
            self.model.images.append(fred)
        
    def image_del(self,uuid):
        matchuuid = None
        if uuid == 'null':
            matchuuid = None
        else:
            matchuuid = uuid
        todelete = []
        for i in range(len(self.model.images)):
            item = self.model.images[i]
            if item.metadata[u'vmi_uid'] == matchuuid:
                todelete.insert(0, i)
        if len(todelete) == 0:
            return False
        for i in todelete:
            del self.model.images[i]
        return True
    def verify(self):
        if 0 == len(self.model.images):
            return False
        requiredmetadata = [u'owner_real_name',
            u'owner_email',
            u'vmic_url',
            u'vmi_url']
        requiredmetadataset = set(requiredmetadata)
        if not requiredmetadataset.issubset(self.model.metadata.keys()):
            return False
        for item in requiredmetadata:
            value = self.model.metadata[item]
            if value == None:
                return False
    def sign(self,signer_key,signer_cert,outfile):
        content = self.view.dumps(self.model)
        
        self.SMIME = SMIME.SMIME()
        self.SMIME.load_key(signer_key,signer_cert)
        buf = BIO.MemoryBuffer(content)        
        p7 = self.SMIME.sign(buf, SMIME.PKCS7_DETACHED)
        buf = BIO.MemoryBuffer(content)
        # Output p7 in mail-friendly format.
        out = BIO.MemoryBuffer()
        #out.write('From: sender@example.dom\n')
        #out.write('To: recipient@example.dom\n')
        #out.write('Subject: M2Crypto S/MIME testing\n')
        self.SMIME.write(out, p7, buf)
        self.message_signed = str(out.read())
        with open(outfile, 'w') as f:
            f.write(self.message_signed )
        # Save the PRNG's state.
def test_things():
    view = vmlistview()
    loadedlist = view.load_file('imagelist.json')
    
    
    avmlistOutput = json.dumps(loadedlist,cls=VMimageListEncoder)
    print "vmimagelist=%s" % (avmlistOutput)
    f = imagemodel(vmi_uid='32455374',
        vmi_url='http://www.yokel.org',
        vmi_hash_sha512='bignum',
        vmi_hypervisor='kvm',
        vmi_description='easy to run vm',
        vmi_os_version='sl6.0201101',
        vmi_os_architecture='i386',
        vmi_disk_size='20e12bytes')
    imageoutput = json.dumps(f,cls=VMimageListEncoder)
    print "xdx%s" % (imageoutput)
    fred = json.loads(imageoutput,object_hook=VMimageDecoder)
    imageoutput = json.dumps(f,cls=VMimageListEncoder)
    print "xdx%s" % (imageoutput)
    avmlist = listmodel(owner_real_name="Owen Synge",
        owner_email='owen.synge@yokel.org',
        vmi_url='www.yokel.org',
        vmic_url='www.yokel.org',
        images=[f])
    avmlistOutput = json.dumps(avmlist,cls=VMimageListEncoder)
    print "vmimagelist=%s" % (avmlistOutput)
    view.save_file(avmlist,'imagelist.json')




def main():
    """Runs program and handles command line options"""
    actions = []
    listcontroler = vmlistcontroler()
    p = optparse.OptionParser()
    p.add_option('-j', '--json', action ='store', help='Path of the json output file')
    p.add_option('-t', '--template', action ='store', help='Path of the json template file')
    p.add_option('-a', '--add', action ='append', help='adds a VM image to the JSON')
    p.add_option('-d', '--delete', action ='append', help='del a VM image to the JSON')
    p.add_option('-g', '--generate', action ='append', help='generates a VM image metadata for image')
    p.add_option('-i', '--image', action ='append', help='Sets the image to generates a VM image metadata')
    p.add_option('-l', '--list', action ='store_true', help='lists VM images in the JSON')
    p.add_option('-k', '--signer_key', action ='store', help='path to signer key')
    p.add_option('-c', '--signer_certificate', action ='store', help='path to signer certificate')
    p.add_option('-s', '--sign', action ='store', help='returns verbose output')
    p.add_option('-f', '--format', action ='store', help='Set the format valid values are JSON and XML')
    
    options, arguments = p.parse_args()
    template = 'imagelist.json'
    json_output = 'imagelist.json'
    add_image_file = []
    del_image_metadata = []
    format = None
    signer_key = os.environ['HOME'] + '/.globus/userkey.pem'
    signer_cert = os.environ['HOME'] + '/.globus/usercert.pem'
    signed_output = None
    list_images = False
    if options.template:
        template = options.template
        actions.append('load_template')
    if options.json:
        json_output = options.json
        actions.append('save')
    if options.add:
        add_image_file = options.add
        actions.append('image_add')
    if options.delete:
        del_image_file = options.delete
        actions.append('image_del')
    if options.list:
        list_images = True
        actions.append('image_list')
    if options.signer_key:
        signer_key = options.signer_key
    if options.signer_certificate:
        signer_cert = options.signer_certificate
    if options.sign:
        actions.append('verify')
        actions.append('sign')
        signed_output = options.sign
    if options.generate:
        generate_list = options.generate
        actions.append('generate')
    if 'generate' in actions:
        image = imagemodel()
        for filename in generate_list:
            with open(filename, 'w') as f:
                json.dump(image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
        
    if 'load_template' in actions:
        listcontroler.load(template)
    if 'image_add' in actions:
        for item in add_image_file:
            listcontroler.image_add(item)
    if 'image_del' in actions:
        for item in del_image_file:
            success = listcontroler.image_del(item)
            if success == False:
                print "Failed to delete image '%s'" % (item)
                sys.exit(1)
    if 'image_list' in actions:
        listcontroler.images_list()
    if 'verify' in actions:
        success = listcontroler.verify()
        if success == False:
            print "Failed to verify valid meta data for image."
            sys.exit(1)
    if 'sign' in actions:
        listcontroler.sign(signer_key,signer_cert,signed_output)
    if 'save' in actions:
        listcontroler.save(json_output)
    #test_things()
if __name__ == "__main__":
    main()
