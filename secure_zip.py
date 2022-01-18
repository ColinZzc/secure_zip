import io
import warnings

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
    将磁盘中未加密的zip文件进行首次加密
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
def decrypt_zip(zip_file_path: str, secure_key_path: str = None, to_file: bool = False, in_place: bool = True) -> bytes:
    """
    解密压缩文件。

    :param zip_file_path: 压缩文件路径
    :param secure_key_path: 密钥存储目录或文件名 默认zip同级目录下与zip文件同名的.key文件。
    :param to_file: 解密数据是否写入文件 默认不写 返回字节流
    :param in_place: 是否替换源文件，只在to_file 为True时生效，默认替换
    :return: 解密后的zip文件字节码
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
    with open(zip_file_path, 'rb') as zip_file:
        data = zip_file.read()

    # 解密
    plant_data = f.decrypt(data)

    if to_file:
        # 写回去 先新建一个zip 防止过程中出现异常破环原始数据
        new_data_file_path = os.path.join(zip_path, 'plain_' + zip_name)
        with open(new_data_file_path, 'wb') as zip_file:
            zip_file.write(plant_data)

        # 删除旧文件 重命名新文件
        if in_place:
            os.remove(zip_file_path)
            os.rename(new_data_file_path, zip_file_path)

    return plant_data


def load_decrypted_zip(zip_file_path: str, secure_key_path: str = None) -> bytes:
    """
    从磁盘中加载加密的zip文件，返回解密后在zip文件字节码

    :param zip_file_path: zip文件路径
    :param secure_key_path: 密钥路径
    :return:
    """
    return decrypt_zip(zip_file_path, secure_key_path)


def to_encrypt_zip(zip_bytes: bytes, zip_file_path: str, secure_key_path: str = None, update_key: bool = False) -> None:
    """

    :param zip_bytes: zip格式的明文字节数据
    :param zip_file_path: 要储存zip文件的路径
    :param secure_key_path: 密钥路径，默认与zip文件在一起的.key文件
    :param update_key: 是否更新密钥 默认不更新
    """
    zip_path, zip_name = os.path.split(zip_file_path)

    if secure_key_path is None:
        secure_key_path = os.path.join(zip_path, zip_name + ".key")  # 文件名+".key"

    key = None
    if not update_key:
        # 获取密钥
        if os.path.exists(secure_key_path):
            with open(secure_key_path, 'rb') as keyFile:
                key = keyFile.read()
        else:
            warnings.warn("key not found in " + secure_key_path + "\n create new key")

    if key is None or update_key:
        # 生成新密钥
        key = Fernet.generate_key()
        # 保存密钥
        with open(secure_key_path, 'wb') as keyFile:
            keyFile.write(key)

    # Fernet
    f = Fernet(key)

    cipher_data = f.encrypt(zip_bytes)
    # 写入新zip文件
    new_data_file_path = os.path.join(zip_path, 'cipher_' + zip_name)
    with open(new_data_file_path, 'wb') as z_file:
        z_file.write(cipher_data)
    # 删除旧文件 重命名新文件
    try:
        os.remove(zip_file_path)
    except FileNotFoundError:
        pass
    os.rename(new_data_file_path, zip_file_path)


if __name__ == '__main__':

    # 压缩算法
    compress_type = zipfile.ZIP_DEFLATED

    data_zip_path = './testData/data.zip'

    # 初始化实验环境
    # 对初始数据进行加密 首次使用时 原始数据从未进行过加密
    encrypt_zip('./testData/data.zip', in_place=True)
    # 现在磁盘中的zip文件已被加密


    # 模拟日常使用
    # 读取zip文件进内存,并完成数据解密
    plant_zip_data = load_decrypted_zip(data_zip_path)

    # 解压缩
    with zipfile.ZipFile(io.BytesIO(plant_zip_data), 'r') as z_file:
        # 存入dict
        files = {}
        for f in z_file.infolist():
            file_name = f.filename
            if not os.path.isdir(file_name):
                files[file_name] = z_file.read(file_name)
    # 所有文件
    print(files.keys())

    # 操作数据
    test = files['test.txt'].decode()
    print(test)
    test = test + "\n new data"
    files['test.txt'] = test.encode()

    # 添加到压缩文件
    new_zip_file_bytes_IO = io.BytesIO()
    with zipfile.ZipFile(new_zip_file_bytes_IO, 'w') as z_file:
        for key in files:
            z_file.writestr(key, files[key], compress_type=compress_type)
    new_zip_file_bytes_IO.seek(0)

    # 加密数据 + 存储
    to_encrypt_zip(new_zip_file_bytes_IO.read(), data_zip_path)

    # 验证 将修改过数据 然后压缩后 加密的zip 解密 可在文件系统中解压缩查看
    decrypt_zip('./testData/data.zip', to_file=True, in_place=False)


