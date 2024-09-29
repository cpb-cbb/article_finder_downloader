import os
import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import fitz

# Edge浏览器驱动路径
driver_path = "./msedgedriver.exe"

# 创建文件夹用于保存PDF
output_folder = "./pdf"
output_folder_abs = os.path.abspath(output_folder)
if not os.path.exists(output_folder_abs):
    os.makedirs(output_folder_abs)

# 创建log.txt文件用于记录下载失败的情况
log_file = "log.txt"
if os.path.exists(log_file):
    os.remove(log_file)


# 清理文件名，使其在Windows中有效
def clean_title(title):
    return re.sub(r'[<>:"/\\|?*]', '', title)


# 使用requests来下载PDF
def download_pdf_via_requests(pdf_url, save_path):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(pdf_url, stream=True, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常

        # 保存PDF文件
        with open(save_path, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 过滤掉保持连接的空块
                    pdf_file.write(chunk)

        print(f"PDF下载完成: {save_path}")
        return True
    except Exception as e:
        print(f"下载PDF失败: {e}")
        return False


# 通过PyMuPDF下载并保存PDF
def save_pdf_from_url(pdf_url, save_path):
    try:
        # 打开PDF链接并保存到本地
        doc = fitz.open(pdf_url)
        doc.save(save_path)
        doc.close()
        return True
    except Exception as e:
        print(f"通过PyMuPDF保存PDF失败: {e}")
        return False


# 启动Edge浏览器
service = Service(driver_path)
options = webdriver.EdgeOptions()
options.add_argument('--headless')  # 隐藏浏览器窗口（可选）
driver = webdriver.Edge(service=service, options=options)


# 定义下载文件的函数
def download_paper(doi, title, current, total):
    global current_paper_title
    cleaned_title = clean_title(title)
    current_paper_title = cleaned_title

    save_path = os.path.join(output_folder_abs, f"{cleaned_title}.pdf")

    if os.path.exists(save_path):
        print(f"PDF已存在: {cleaned_title}.pdf，跳过下载。")
        return

    max_retries = 5
    retries = 0

    while retries < max_retries:
        try:
            sci_hub_url = f"https://sci-hub.gupiaoq.com/{doi}"
            driver.get(sci_hub_url)

            print(f"正在下载第 {current}/{total} 篇文章: {title}")

            # 显式等待iframe出现
            iframe_elements = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
            )

            # 依次检查每个iframe，寻找实际的PDF
            pdf_url = None
            for iframe in iframe_elements:
                src = iframe.get_attribute('src')
                if src and "pdf" in src:  # 可能的PDF链接
                    pdf_url = src
                    break

            if not pdf_url:
                print("未找到PDF链接，可能是广告或页面问题。")
                retries += 1
                time.sleep(2)
                continue

            print(f"找到PDF URL: {pdf_url}")
            time.sleep(2)  # 等待加载

            # 尝试通过requests下载PDF
            success = download_pdf_via_requests(pdf_url, save_path)

            # 检查下载的文件大小是否小于10KB
            if success and os.path.exists(save_path):
                file_size_kb = os.path.getsize(save_path) / 1024  # 文件大小单位为KB
                if file_size_kb < 10:
                    print(f"文件 {cleaned_title}.pdf 大小为 {file_size_kb}KB，认为下载不成功。正在重试...")
                    success = False
                else:
                    print(f"成功下载并验证: {cleaned_title}.pdf")
                    break
            else:
                print(f"下载失败或未找到文件: {cleaned_title}.pdf。正在重试...")

        except Exception as e:
            print(f"下载文章 {title} 时出错: {e}。正在重试...")

        retries += 1
        time.sleep(2)

    # 如果经过5次重试下载失败并且文件小于10KB，删除该文件
    if retries == max_retries:
        if os.path.exists(save_path) and os.path.getsize(save_path) / 1024 < 10:
            os.remove(save_path)  # 删除文件
            print(f"删除文件 {cleaned_title}.pdf 因为多次尝试后仍下载失败且文件小于10KB")
        with open(log_file, 'a') as log:
            log.write(f"下载失败: {title} (DOI: {doi})，重试 {max_retries} 次后仍失败。时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.flush()  # 确保日志内容即时写入文件
        print(f"下载 {title} 失败，重试 {max_retries} 次后跳过。")


def main():
    csv_file_path = "doi_list.csv"
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
    except:
        df = pd.read_csv(csv_file_path, encoding='gbk')

    total_papers = len(df)

    for index, row in df.iterrows():
        doi = row['DOI']
        title = row['Title']
        download_paper(doi, title, index + 1, total_papers)

    driver.quit()


if __name__ == '__main__':
    main()
