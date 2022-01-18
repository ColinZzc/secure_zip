from my_time import timer
import zipfile
import gzip
import shutil
import os
import tarfile
from cryptography.fernet import Fernet


def cipherDemo():
    # Put this somewhere safe!
    key = Fernet.generate_key()
    print(key)
    f = Fernet(key)
    token = f.encrypt(b"A really secret message. Not for prying eyes.")
    print(token)
    p = f.decrypt(token)
    print(p)


def zipDemo():
    dataFilePath = 'Data.zip'
    # 读进来

    # 压缩文件
    zFiles = zipfile.ZipFile(dataFilePath, 'r')
    # zinfo 对象
    zInfos = zFiles.infolist()
    # data ！前提：压缩文件中不存在重名文件(包含路径)
    data = {}
    for zInfo in zInfos:
        if zInfo.is_dir():
            continue
        fileName = zInfo.filename
        data[fileName] = zFiles.read(fileName)
    zFiles.close()

    # 写回去 先新建一个zip 不然会包含重复名称 出现异常也会破环原始数据
    newDataFilePath = 'new_' + dataFilePath
    zFiles = zipfile.ZipFile(newDataFilePath, 'w')
    for key in data:
        zFiles.writestr(key, data[key], compress_type=zipfile.ZIP_DEFLATED)
    zFiles.close()

    # 删除旧文件 重命名新文件
    os.remove(dataFilePath)
    os.rename(newDataFilePath, dataFilePath)


@timer
def encrypt_data_in_zip(zip_file_path: str, secure_key_path: str = None, in_place: bool = True):
    """
    加密zip文件中的数据
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
    z_files = zipfile.ZipFile(zip_file_path, 'r')
    # zinfo 对象
    z_infos = z_files.infolist()
    # data ！前提：压缩文件中不存在重名文件(包含路径)
    # 读取数据
    data = {}
    for zInfo in z_infos:
        if zInfo.is_dir():
            continue
        file_name = zInfo.filename
        data[file_name] = z_files.read(file_name)
    z_files.close()

    # 加密后 写回去 先新建一个zip 不然会包含重复名称 过程中出现异常也会破环原始数据
    new_data_file_path = os.path.join(zip_path, 'cipher_' + zip_name)
    z_files = zipfile.ZipFile(new_data_file_path, 'w')
    for key in data:
        # 加密
        cipher_data = f.encrypt(data[key])
        # 压缩并写入
        z_files.writestr(key, cipher_data, compress_type=compress_type)
    z_files.close()

    # 删除旧文件 重命名新文件
    if in_place:
        os.remove(zip_file_path)
        os.rename(new_data_file_path, zip_file_path)


@timer
def decrypt_data_in_zip(zip_file_path: str, secure_key_path: str = None, in_place: bool = True):
    """
    解密压缩文件中的数据。

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
    z_files = zipfile.ZipFile(zip_file_path, 'r')
    # zinfo 对象
    z_infos = z_files.infolist()
    # 读取数据
    data = {}
    for zInfo in z_infos:
        if zInfo.is_dir():
            continue
        file_name = zInfo.filename
        data[file_name] = z_files.read(file_name)
    z_files.close()

    # 解密后 写回去 先新建一个zip 不然会包含重复名称 过程中出现异常也会破环原始数据
    new_data_file_path = os.path.join(zip_path, 'plain_' + zip_name)
    z_files = zipfile.ZipFile(new_data_file_path, 'w')
    for key in data:
        # 解密
        plant_data = f.decrypt(data[key])
        # 压缩并写入
        z_files.writestr(key, plant_data, compress_type=compress_type)
    z_files.close()

    # 删除旧文件 重命名新文件
    if in_place:
        os.remove(zip_file_path)
        os.rename(new_data_file_path, zip_file_path)


if __name__ == '__main__':
    compress_type = zipfile.ZIP_DEFLATED

    encrypt_data_in_zip('./testData/data.zip', in_place=False)
    decrypt_data_in_zip('./testData/cipher_data.zip', secure_key_path='./testData/data.zip.key', in_place=False)
