import sys
import M2Crypto.SMIME 
import M2Crypto.BIO 
import M2Crypto.SMIME

if float(sys.version[:3]) >= 2.6:
    import json
else:
    # python 2.4 or 2.5 can also import simplejson
    # as working alternative to the json included.
    import simplejson as json

signer_key = "userkey.pem"
signer_cert = "usercert.pem"
outfile = "imagelist.smime"

model = {
  "hv:imagelist": {
    "hv:uri": "https://example.org/example-image-list.image_list",
    "hv:version": "1",
    "dc:description": "a README example of an image list",
    "dc:date:created": "2011-03-10T17:09:12Z",
    "dc:source": "example.org",
    "hv:endorser": {
      "hv:x509": {
        "hv:dn": "/C=DE/O=GermanGrid/OU=DESY/CN=Owen Synge",
        "dc:creator": "Owen Synge",
        "hv:email": "owen.synge@desy.de",
        "hv:ca": "/C=DE/O=GermanGrid/CN=GridKa-CA"
      }
    },
    "dc:date:expires": "2011-04-07T17:09:12Z",
    "hv:images": [
      {
        "hv:image": {
          "hv:uri": "http://example.org/example-image.img",
          "sl:osversion": "SL 5.5",
          "sl:comments": "Vanila install with contextulization scripts",
          "hv:version": "1",
          "dc:description": "This is an README example VM",
          "sl:checksum:sha512": "8b4c269a60da1061b434b696c4a89293bea847b66bd8ba486a914d4209df651193ee8d454f8231840b7500fab6740620c7111d9a17d08b743133dc393ba2c0d4",
          "hv:size": 2147483648,
          "sl:arch": "x86_64",
          "hv:hypervisor": "kvm",
          "dc:identifier": "488dcdc4-9ab1-4fc8-a7ba-b7a5428ecb3d",
          "sl:os": "Linux",
          "dc:title": "README example VM"
        }
      }
    ],
    "dc:identifier": "4e186b44-2c64-40ea-97d5-e9e5c0bce059",
    "dc:title": "README example"
  }
}


# Note the dumps command options ",sort_keys=True, indent=2" 
# are optional but make things easier for humans when signing.
content = json.dumps(model,sort_keys=True, indent=2)
smime = M2Crypto.SMIME.SMIME()
smime.load_key(signer_key,signer_cert)
buf = M2Crypto.BIO.MemoryBuffer(content)        
p7 = smime.sign(buf,M2Crypto.SMIME.PKCS7_DETACHED)
buf = M2Crypto.BIO.MemoryBuffer(content)
out = M2Crypto.BIO.MemoryBuffer()
smime.write(out, p7, buf)
message_signed = str(out.read())
f = open(outfile, 'w')
f.write(message_signed)
