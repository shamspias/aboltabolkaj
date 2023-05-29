import itertools
import msoffcrypto 

def try_open(password):
    try:
        file = msoffcrypto.OfficeFile(open("secured.docx", "rb"))
        file.load_key(password=password)
        decrypted = open("decrypted.docx", "wb")
        file.decrypt(decrypted)
        return True
    except:
        return False

charset = "abc123"  # This should be all possible characters
for password_length in range(1, 6):  # Adjust this range for longer passwords
    for password_tuple in itertools.product(charset, repeat=password_length):
        password = "".join(password_tuple)
        if try_open(password):
            print("Found the password: ", password)
            break
