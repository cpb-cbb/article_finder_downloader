import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import os

# 设置EdgeDriver路径
edge_driver_path = 'msedgedriver.exe'  # 替换为你的实际驱动路径

# 初始化Edge WebDriver
service = EdgeService(executable_path=edge_driver_path)
driver = webdriver.Edge(service=service)


# 原代码部分...

def remove_duplicates(output_file):
    """从CSV文件中移除重复的DOI，'DOI not found'的条目除外。"""
    # 加载生成的CSV文件
    df = pd.read_csv(output_file, encoding='utf-8')

    # 分离出"DOI not found"的条目
    not_found_df = df[df['DOI'] == 'DOI not found']

    # 仅从有效的DOI中移除重复项（排除"DOI not found"）
    found_df = df[df['DOI'] != 'DOI not found'].drop_duplicates(subset='DOI')

    # 合并清理后的数据与"DOI not found"的条目
    df_cleaned = pd.concat([found_df, not_found_df])

    # 将清理后的数据保存回同一CSV文件
    df_cleaned.to_csv(output_file, index=False, encoding='utf-8')
    print(f"重复项已移除。最终文件已保存为 {output_file}")


# 检查是否已经在文章页面上的函数
def is_article_page(soup):
    """检查当前页面是否为文章页面。"""
    title_element = soup.find("h1", class_="heading-title")
    doi_element = soup.find("span", class_="citation-doi")
    return title_element is not None and doi_element is not None


# 从PubMed抓取标题和DOI的函数
def fetch_pubmed_info(info):
    base_url = "https://pubmed.ncbi.nlm.nih.gov/"
    query = f"{info}"

    # 执行搜索
    driver.get(base_url)
    search_box = driver.find_element(By.NAME, "term")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    # 解析页面
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 检查是否已经在文章页面
    if is_article_page(soup):
        # 已经在文章页面，抓取标题和DOI
        title_element = soup.find("h1", class_="heading-title")
        title = title_element.get_text(strip=True) if title_element else "未找到标题"

        # 提取DOI
        doi_element = soup.find("span", class_="citation-doi")
        doi = doi_element.get_text(strip=True).replace('doi: ', '') if doi_element else "DOI未找到。"

    else:
        # 如果不是，点击第一个搜索结果然后抓取
        result_link = soup.find("a", class_="docsum-title")
        if result_link:
            first_result_url = result_link['href']
            driver.get(f"https://pubmed.ncbi.nlm.nih.gov{first_result_url}")
            # 等待文章页面加载

            # 用文章页面内容更新soup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # 提取标题和DOI
            title_element = soup.find("h1", class_="heading-title")
            title = title_element.get_text(strip=True) if title_element else "未找到标题"

            # 提取DOI
            doi_element = soup.find("span", class_="citation-doi")
            doi = doi_element.get_text(strip=True).replace('doi: ', '') if doi_element else "DOI未找到。"
        else:
            title = "未找到标题"
            doi = "DOI未找到。"

    return title, doi


def write_to_csv(row_data, output_file):
    """将一行数据写入CSV文件。"""
    df_row = pd.DataFrame([row_data], columns=['info', 'Title', 'DOI'])
    # 检查文件是否存在；如果不存在，写入表头
    if not os.path.exists(output_file):
        df_row.to_csv(output_file, index=False, mode='w', header=True, encoding='utf-8')
    else:
        df_row.to_csv(output_file, index=False, mode='a', header=False, encoding='utf-8')


def main():
    input_file = 'input.csv'
    output_file = 'doi_list.csv'

    # 加载CSV数据
    try:
        df = pd.read_csv(input_file, encoding='utf-8', header=None)
    except:
        df = pd.read_csv(input_file, encoding='gbk', header=None)

    # 文章总数
    total_articles = len(df)

    # 遍历每一行并抓取数据
    for i, row in df.iterrows():
        info = row[0]

        # 获取文章信息
        title, doi = fetch_pubmed_info(info)
        doi = doi[:-1]  # 去掉DOI末尾的空格或换行符

        # 在抓取数据后立即写入CSV
        write_to_csv([info, title, doi], output_file)

        # 显示进度
        progress = (i + 1) / total_articles * 100
        print(f"标题: {title}\nDOI: {doi}\n进度: {progress:.2f}% ({i + 1}/{total_articles})")

    # 在所有条目写入后移除重复项
    remove_duplicates(output_file)

    # 关闭Edge浏览器
    driver.quit()


if __name__ == '__main__':
    main()
