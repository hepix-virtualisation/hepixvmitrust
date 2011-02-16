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
        
        self.metadata = {u'vmi_uid' : vmi_uid,
            u'vmi_url' : vmi_url,
            u'vmi_hash_sha512' :vmi_hash_sha512,
            u'vmi_hypervisor' : vmi_hypervisor,
            u'vmi_description' : vmi_description,
            u'vmi_os_version' : vmi_os_version,
            u'vmi_os_architecture' : vmi_os_architecture,
            u'vmi_disk_size' : vmi_disk_size}


class listmodel:
    interestingkeys = set([u'vmi_uid'])
    def __init__(self,owner_real_name=None,
        owner_email=None,
        vmic_url=None,
        images=[]):
        self.metadata = {
            u'owner_real_name' : owner_real_name,
            u'owner_email' : owner_email,
            u'vmic_url' : vmic_url,
            }
        self.images = images





class VMimageListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, imagemodel):
            return {u'metadata' : obj.metadata}
        if isinstance(obj, listmodel):
            imagelist = []
            for i in obj.images:
                tmp_data = self.default(i)
                if tmp_data == None:
                    return json.JSONEncoder.default(self, obj)
                else:
                    imagelist.append(self.default(i))
            return {u'metadata' : obj.metadata, u'images' : imagelist}
        return json.JSONEncoder.default(self, obj)

def VMimageDecoder(dct):
    if not u'metadata' in dct.keys():
        return None
    metadata = dct[u'metadata']
    if metadata == None:
        print "coding error=%s" % (dct)
        
        return None
    requiredmetadata = [u'vmi_uid',
        u'vmi_url',
        u'vmi_hash_sha512',
        u'vmi_hypervisor',
        u'vmi_description',
        u'vmi_os_version',
        u'vmi_os_architecture',
        u'vmi_disk_size']
    requiredmetadataset = set(requiredmetadata)
    if not requiredmetadataset.issubset(metadata.keys()):
        
        return None
    return imagemodel(vmi_uid=metadata[u'vmi_uid'],
        vmi_url=metadata[u'vmi_url'],
        vmi_hash_sha512=metadata[u'vmi_hash_sha512'],
        vmi_hypervisor=metadata[u'vmi_hypervisor'],
        vmi_description=metadata[u'vmi_description'],
        vmi_os_version=metadata[u'vmi_os_version'],
        vmi_os_architecture=metadata[u'vmi_os_architecture'],
        vmi_disk_size=metadata[u'vmi_disk_size']
        )

def VMimageListDecoder(dct):
    requiredkeys = [u'metadata', u'images']
    requiredkeysset = set(requiredkeys)
    if not requiredkeysset.issubset(dct.keys()):
        return False
    listmetadata = dct[u'metadata']
    requiredmetadata = [u'owner_real_name',
        u'owner_real_name',
        u'owner_email',
        u'vmic_url']
    requiredmetadataset = set(requiredmetadata)
    if not requiredmetadataset.issubset(listmetadata.keys()):
        return False
    images = dct[u'images']
    allimages = []
    for image in images:
        translatedimage = VMimageDecoder(image)
        if not translatedimage == None:
            allimages.append(translatedimage)
    # Now we generate the output
    output = listmodel(owner_real_name=listmetadata[u'owner_real_name'],
        owner_email=listmetadata[u'owner_email'],
        vmic_url=listmetadata[u'vmic_url'],
        images=allimages
        )
    return output

def file_extract_metadata(file_name):
    if file_name == None:
        return
    if not os.path.isfile(file_name):
        return None
    m = hashlib.sha512()
    filelength = 0
    for line in open(file_name,'r'):
        filelength += len(line)
        m.update(line) 
    return {u'vmi_disk_size' : filelength, 
            u'vmi_hash_sha512' : m.hexdigest()}



class vmlistview:
    def load_file(self,filename):
        loadedfile = None
        fp = open(filename, 'r')

        loadedfile = json.load(fp)
        decoded_image = VMimageListDecoder(loadedfile)
        if decoded_image == False:
            return False
        return decoded_image
        
    def save_file(self,entry,filename):
        f = open(filename, 'w')
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
        f = open(filename, 'r')
        json_stuff = json.load(f)
        fred= VMimageDecoder(json_stuff)
        if fred == None:
            return False
        self.model.images.append(fred)
        return True
        
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
            print "No images in data no point signing"
            return False
        requiredmetadata = [u'owner_real_name',
            u'owner_email',
            u'vmic_url']
        requiredmetadataset = set(requiredmetadata)
        if not requiredmetadataset.issubset(self.model.metadata.keys()):
            print "missing metadata"
            return False
        
        for item in requiredmetadata:
            value = self.model.metadata[item]
            if value == None:
                print "image list metadata set to null '%s'" % (item)
                return False
        return True
        
    def sign(self,signer_key,signer_cert,outfile):
        content = self.view.dumps(self.model)
        
        self.SMIME = SMIME.SMIME()
        self.SMIME.load_key(signer_key,signer_cert)
        buf = BIO.MemoryBuffer(content)        
        p7 = self.SMIME.sign(buf, SMIME.PKCS7_DETACHED)
        buf = BIO.MemoryBuffer(content)
        out = BIO.MemoryBuffer()
        self.SMIME.write(out, p7, buf)
        self.message_signed = str(out.read())
        f = open(outfile, 'w')
        f.write(self.message_signed )
        # Save the PRNG's state.
    def generate(self,filename,imagepath=None):
        output_image = None

        if imagepath!=None:

            metadata = file_extract_metadata(imagepath)
            if metadata == None:
                print "error reading file '%s'." % (imagename)
                sys.exit(1)
            output_image = imagemodel(
                vmi_hash_sha512= metadata[u'vmi_hash_sha512'],
                vmi_disk_size=metadata[u'vmi_disk_size'])
        else:
            output_image = imagemodel()
        f = open(filename, 'w')
        json.dump(output_image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)

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


# User interface

def pairsNnot(list_a,list_b):
    len_generate_list = len(list_a)
    len_image_list = len(list_b)
    ocupies_generate_list = set(range(len_generate_list))
    ocupies_image_list = set(range(len_image_list))
    ocupies_pairs = ocupies_image_list.intersection(ocupies_generate_list)
    diff_a = ocupies_generate_list.difference(ocupies_image_list)
    diff_b = ocupies_image_list.difference(ocupies_generate_list)
    arepairs = []
    for i in ocupies_pairs:
        arepairs.append([list_a[i],list_b[i]])
    notpairs_a = []
    for i in diff_a:
        notpairs_a.append(list_a[i])
    notpairs_b = []
    for i in diff_b:
        notpairs_b.append(list_b[i])
    
    return arepairs,notpairs_a,notpairs_b



def main():
    """Runs program and handles command line options"""
    actions = set([])
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
    generate_list = []
    add_image_file = []
    del_image_metadata = []
    format = None
    signer_key = os.environ['HOME'] + '/.globus/userkey.pem'
    signer_cert = os.environ['HOME'] + '/.globus/usercert.pem'
    signed_output = None
    list_images = False
    imagelist = []
    if options.template:
        template = options.template
        actions.add('load_template')
    if options.json:
        json_output = options.json
        actions.add('save')
    if options.add:
        add_image_file = options.add
        actions.add('image_add')
    if options.delete:
        del_image_file = options.delete
        actions.add('image_del')
    if options.list:
        list_images = True
        actions.add('image_list')
    if options.signer_key:
        signer_key = options.signer_key
    if options.signer_certificate:
        signer_cert = options.signer_certificate
    if options.sign:
        actions.add('verify')
        actions.add('sign')
        signed_output = options.sign
    if options.generate:
        generate_list = options.generate
        actions.add('generate')
    if options.format:
        print "Currently only supports JSON output RDF XML output may come later"
    if options.image:
        imagelist = options.image
        actions.add('generate')
        
    # Now process the actions.
    
    if actions.__contains__('generate'):
        pairs, extra_gens ,extra_images = pairsNnot(generate_list,imagelist)
        if len(extra_images) > 0:
            print "error images and no target"
        for paired_items in pairs:    
            listcontroler.generate(paired_items[0],paired_items[1])
        for gen_it in extra_gens:
            listcontroler.generate(gen_it)
    if actions.__contains__('load_template'):
        listcontroler.load(template)
    if actions.__contains__('image_add'):
        for item in add_image_file:
            listcontroler.image_add(item)
    if actions.__contains__('image_del'):
        for item in del_image_file:
            success = listcontroler.image_del(item)
            if success == False:
                print "Failed to delete image '%s'" % (item)
                sys.exit(1)
    if actions.__contains__('image_list'):
        listcontroler.images_list()
    if actions.__contains__('verify'):
        success = listcontroler.verify()
        if success == False:
            print "Failed to verify valid meta data for image."
            sys.exit(1)
    if actions.__contains__('sign'):
        listcontroler.sign(signer_key,signer_cert,signed_output)
    if actions.__contains__('save'):
        listcontroler.save(json_output)
    #test_things()
if __name__ == "__main__":
    main()
