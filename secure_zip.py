from my_time import timer
import zipfile
import gzip
import shutil
import os
import tarfile
from cryptography.fernet import Fernet


@timer
def encrypt_zip(zip_file_path: str, secure_key_path: str = None, in_place: bool = True):
    """
    加密zip文件
    指定压缩文件，首次进行加密。
    同时生成密钥文件。

    :param zip_file_path: 压缩文件路径 压缩文件中不能包含路径相同的重名文件
    :param secure_key_path: 密钥存储目录或文件名 默认与zip同级目录与zip文件同名的.key文件. 存在会覆盖
    :param in_place: 是否替换源文件，默认是
    """
    zip_path, zip_name = os.path.split(zip_file_path)
    # 密钥文件路径
    if secure_key_path is None:
        secure_key_name = zip_name + ".key"  # 文件名+".key"
        secure_key_path = os.path.join(zip_path, secure_key_name)
    elif os.path.isdir(secure_key_path):
        secure_key_path = os.path.join(secure_key_path, zip_name + ".key")

    # 生成密钥 Put this somewhere safe!
    key = Fernet.generate_key()
    # 保存密钥
    with open(secure_key_path, 'wb') as keyFile:
        keyFile.write(key)

    # Fernet
    f = Fernet(key)
    # 读压缩文件
    with open(zip_file_path, 'rb') as z_file:
        data = z_file.read()
    # 加密
    cipher_data = f.encrypt(data)
    # 写入新zip文件
    new_data_file_path = os.path.join(zip_path, 'cipher_' + zip_name)
    with open(new_data_file_path, 'wb') as z_file:
        z_file.write(cipher_data)

    # 删除旧文件 重命名新文件
    if in_place:
        os.remove(zip_file_path)
        os.rename(new_data_file_path, zip_file_path)


@timer
def decrypt_zip(zip_file_path: str, secure_key_path: str = None, in_place: bool = True):
    """
    解密压缩文件。

    :param zip_file_path: 压缩文件路径
    :param secure_key_path: 密钥存储目录或文件名 默认zip同级目录下与zip文件同名的.key文件。
    :param in_place: 是否替换源文件，默认是
    """
    # 密钥文件路径

    zip_path, zip_name = os.path.split(zip_file_path)

    if secure_key_path is None:
        secure_key_path = os.path.join(zip_path, zip_name + ".key")  # 文件名+".key"

    # 获取密钥
    if os.path.exists(secure_key_path):
        with open(secure_key_path, 'rb') as keyFile:
            key = keyFile.read()
    else:
        raise Exception("key not found in "+secure_key_path)

    # Fernet
    f = Fernet(key)
    # 读压缩文件
    with open(zip_file_path, 'rb') as z_file:
        data = z_file.read()

    # 解密
    plant_data = f.decrypt(data)

    # 写回去 先新建一个zip 防止过程中出现异常破环原始数据
    new_data_file_path = os.path.join(zip_path, 'plain_' + zip_name)
    with open(new_data_file_path, 'wb') as z_file:
        z_file.write(plant_data)


    # 删除旧文件 重命名新文件
    if in_place:
        os.remove(zip_file_path)
        os.rename(new_data_file_path, zip_file_path)


if __name__ == '__main__':
    compress_type = zipfile.ZIP_DEFLATED

    # encrypt_zip('./testData/data.zip', in_place=False)
    # decrypt_zip('./testData/cipher_data.zip', secure_key_path='./testData/data.zip.key', in_place=False)
