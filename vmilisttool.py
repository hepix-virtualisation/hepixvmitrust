#!/usr/bin/env python

import codecs
import optparse
import os
import sys
import hashlib
import os.path
# needed to the signing of images.
from M2Crypto import BIO, Rand, SMIME
import uuid
# simplejson is included with Python 2.6 and above
# with the name json
if float(sys.version[:3]) >= 2.6:
    import json
else:
    # python 2.4 or 2.5 can also import simplejson
    # as working alternative to the json included.
    import simplejson as json

import datetime

endorser_required_metadata = [u'hv:ca',
        u'hv:dn',
        u'hv:email',
        u'dc:creator',
    ]
endorser_required_metadata_set = set(endorser_required_metadata)

image_required_metadata = [u'dc:title',
        u'dc:description',
        u'hv:size',
        u'sl:checksum:sha512',
        u'sl:arch',
        u'hv:uri',
        u'dc:identifier',
        u'sl:os',
        u'sl:osversion',
        u'sl:comments',
        u'hv:hypervisor',
        u'hv:version',
    ]
image_required_metadata_set = set(image_required_metadata)


imagelist_required_metadata = [u'dc:date:created',
        u'dc:date:expires',
        u'dc:identifier',
        u'dc:description',
        u'dc:title',
        u'dc:source',
        u'hv:version',
    ]
imagelist_required_metadata_set = set(imagelist_required_metadata)


class endorsermodel:
    def __init__(self,metadata = {}):
        self.metadata = metadata


class imagemodel:    
    def __init__(self,metadata = {}):
        self.metadata = metadata

class listmodel:
    interestingkeys = set([u'vmi_uid'])
    def __init__(self,metadata = {},images=[],endorser=endorsermodel()):
        self.endorser = endorser
        self.metadata = metadata
        self.images = images

        
class VMimageListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, endorsermodel):
            return self.vm_endorser_encode(obj)
        if isinstance(obj, imagemodel):
            return self.vm_image_encode(obj)
        if isinstance(obj, listmodel):
            return self.vm_imagelist_encode(obj)            
        return json.JSONEncoder.default(obj)

    def vm_image_encode(self, obj):
        if not obj.metadata.has_key(u'dc:identifier'):
            obj.metadata[u'dc:identifier'] = str(uuid.uuid4())
        for field in image_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        return {u'hv:image' : obj.metadata}

    def vm_imagelist_encode(self, obj):    
        if not obj.metadata.has_key(u'dc:identifier'):
            obj.metadata[u'dc:identifier'] = str(uuid.uuid4())
        if not obj.metadata.has_key(u'dc:date:created'):
            now = datetime.datetime.utcnow()
            obj.metadata[u'dc:date:created'] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if not obj.metadata.has_key(u'dc:date:expires'):
            now = datetime.datetime.utcnow()
            servicelength = datetime.timedelta(weeks=4)
            expiry = now + servicelength
            obj.metadata[u'dc:date:expires'] = expiry.strftime("%Y-%m-%dT%H:%M:%SZ")
        imagelist = []
        for i in obj.images:
            tmp_data = self.default(i)
            if tmp_data == None:
                return json.JSONEncoder.default(self, obj)
            else:
                imagelist.append(self.default(i))
        for field in imagelist_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        output = {u'hv:images' : imagelist,
            u'hv:endorser' : self.default(obj.endorser)}
        for key in obj.metadata.keys():
            output[key] = obj.metadata[key]
        return output
    
    def vm_endorser_encode(self, obj):
        for field in endorser_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        return {u'hv:x509' : obj.metadata}

def VMendorserDecoder(dct):
    if not u'hv:x509' in dct.keys():
        return None
    metadata = dct[u'hv:x509']
    if metadata == None:
        print "coding error=%s" % (dct)
        return None
    if not endorser_required_metadata_set.issubset(metadata.keys()):    
        print "coding error2=%s" % (dct)
        return None
    #print "VMendorserDecoder.metadata=%s" % (metadata)
    return endorsermodel(metadata=metadata)

def VMimageDecoder(dct):
    if not u'hv:image' in dct.keys():
        return None
    metadata = dct[u'hv:image']
    if metadata == None:
        print "coding error=%s" % (dct)
        return None
    if not image_required_metadata_set.issubset(metadata.keys()):    
        print "coding error2=%s" % (dct)
        return None
    return imagemodel(metadata=metadata)

def VMimageListDecoder(dct):
    if not imagelist_required_metadata_set.issubset(dct.keys()):
        return None    
    if not dct.has_key(u'hv:endorser'):
        return None
    if not dct.has_key(u'hv:images'):
        return None
    endorser_dct = dct[u'hv:endorser']
    imagelist = dct[u'hv:images']
    allimages = []
    for image in imagelist:
        translatedimage = VMimageDecoder(image)
        if not translatedimage == None:
            allimages.append(translatedimage)
    imagelistmetadata = {}
    endorser = VMendorserDecoder(endorser_dct)
    if endorser == None:
        return None
    for field in imagelist_required_metadata:
        imagelistmetadata[field] = dct[field]
    # Now we generate the output
    output = listmodel(metadata = imagelistmetadata,
        endorser = endorser,
        images = allimages
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
    return {u'hv:size' : filelength, 
            u'sl:checksum:sha512' : m.hexdigest()}



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
        
        if not imagelist_required_metadata_set.issubset(self.model.metadata.keys()):
            print "missing metadata"
            return False
        
        for item in imagelist_required_metadata:
            value = self.model.metadata[item]
            if value == None or value == "":
                print "image list metadata set to none '%s'" % (item)
                return False
        for image in self.model.images:
            for item in image_required_metadata:
                value = image.metadata[item]
                if value == None or value == "":
                    print "image metadata set to none '%s'" % (item)
                    return False
        for item in endorser_required_metadata:
            value = self.model.endorser.metadata[item]
            if value == None or value == "":
                print "endorser metadata set to none '%s'" % (item)
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
            output_image = imagemodel(metadata=metadata)
        else:
            output_image = imagemodel()
        f = open(filename, 'w')
        json.dump(output_image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)

def test_things():
    image = endorsermodel()
    f = open("endorser", 'w')
    json.dump(image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("endorser", 'r')
    json_stuff = json.load(f)
    print 'dsadasd'
    fred= VMendorserDecoder(json_stuff)
    print 'dsadasd'
    print fred.metadata
    
def test_things2():
    image = imagemodel()
    f = open("fred", 'w')
    json.dump(image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("fred", 'r')
    json_stuff = json.load(f)
    fred= VMimageDecoder(json_stuff)
    print fred.metadata
    print 'dsadasd'

def test_things3():
    list_mode = listmodel()
    f = open("listmodel", 'w')
    json.dump(list_mode, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("listmodel", 'r')
    json_stuff = json.load(f)
    fred= VMimageDecoder(json_stuff)
    print fred.metadata
    print 'dsadasd'
def test_things4():
    view = vmlistview()
    loadedlist = view.load_file('imagelist.json')
    
    
    avmlistOutput = json.dumps(loadedlist,cls=VMimageListEncoder)
    print "vmimagelist=%s" % (type(avmlistOutput))
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

def test_things5():
    view = vmlistview()
    loadedlist = view.load_file('/tmp/foo2.json')
    print "loadedlist=%s" % (loadedlist)
    print "loadedlist.metadata=%s" % (loadedlist.metadata)
    print "loadedlist.endorser=%s" % (loadedlist.endorser)
    print "loadedlist.images=%s" % (loadedlist.images)
    
    avmlistOutput = json.dumps(loadedlist,cls=VMimageListEncoder, sort_keys=True, indent=4)
    print "vmimagelist=%s" % (avmlistOutput)
    
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
    #test_things5()
if __name__ == "__main__":
    main()
