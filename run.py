import os
import time
import download
import get_doi


# 等待输出文件生成的函数
def wait_for_file(file_path, timeout=300, check_interval=5):
    """
    等待文件生成，检查每隔 `check_interval` 秒一次，如果超过 `timeout` 时间（以秒为单位）没有生成，则抛出超时错误。
    """
    start_time = time.time()
    while not os.path.exists(file_path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"等待文件生成超时: {file_path}")
        time.sleep(check_interval)
    print(f"文件生成: {file_path}")


# 检查是否已经有doi_list.csv文件
if os.path.exists('doi_list.csv'):
    print("已检测到doi_list.csv，跳过查询步骤。")
else:
    print("查询doi...")
    try:
        get_doi.main()
    except Exception as e:
        input(f'出现错误，请确认csv文件中没有逗号且只有一列。若存在逗号请将逗号全部替换为空格再试。\n错误：{e}')
    wait_for_file('doi_list.csv')
    print("查询完毕，查询结果在doi_list.csv中。")

# 执行下载操作
print("下载中...")
download.main()
print("下载完毕，所有pdf在/pdf文件夹中，错误日志在log.txt中。")
