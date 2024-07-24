# 必要的依赖库
import requests
from datetime import datetime, timedelta, timezone
import os


class GitHubActionsManager:
    def __init__(self, repo_url, token):
        self.repo_url = repo_url  # GitHub仓库URL
        self.token = token  # GitHub个人访问令牌
        self.runs_url = f"{self.repo_url}/actions/runs"  # 获取运行记录的URL
        self.current_time = datetime.now(timezone.utc)  # 获取当前时间

    def get_workflow_runs(self, url):
        # 发送GET请求获取工作流运行记录
        response = requests.get(url, headers={"Authorization": f"token {self.token}"})
        if response.status_code == 200:  # 如果请求成功
            return response.json()["workflow_runs"]  # 返回运行记录列表
        else:  # 如果请求失败
            self.log(f"Failed to fetch runs from {url}. Status code: {response.status_code}")  # 打印错误信息
            return []  # 返回空列表

    def delete_run(self, run_id):
        delete_url = f"{self.runs_url}/{run_id}"  # 构建删除运行记录的URL
        # 发送DELETE请求删除指定ID的运行记录
        response = requests.delete(delete_url, headers={"Authorization": f"token {self.token}"})
        if response.status_code == 204:  # 如果删除成功
            self.log(f"Deleted run with ID {run_id}")  # 打印删除成功的消息
        else:  # 如果删除失败
            self.log(f"Failed to delete run with ID {run_id}. Status code: {response.status_code}")  # 打印错误信息

    def delete_old_runs(self):
        while True:  # 无限循环，直到没有符合条件的运行记录为止
            next_page = self.runs_url  # 初始化下一页的URL为第一页
            page_number = 1  # 初始化页数计数器
            any_deleted = False  # 标记是否有记录被删除

            while next_page:  # 循环直到没有下一页
                self.log(f"Fetching page {page_number}")  # 输出当前的页数
                # 发送GET请求获取一页工作流运行记录
                response = requests.get(next_page, headers={"Authorization": f"token {self.token}"})
                if response.status_code == 200:  # 如果请求成功
                    data = response.json()  # 将响应数据转换为JSON格式
                    runs = data["workflow_runs"]  # 获取运行记录列表
                    next_page = response.links.get("next", {}).get("url")  # 获取下一页的URL
                    page_number += 1  # 增加页数计数器

                    for run in runs:  # 遍历每条运行记录
                        # 将运行记录的创建时间转换为UTC时间
                        run_time = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        # 计算当前时间与运行记录创建时间的差值
                        time_difference = self.current_time - run_time
                        if time_difference > timedelta(hours=hour_count):  # 如果差值超过指定小时 默认168小时
                            self.delete_run(run["id"])  # 删除运行记录
                            any_deleted = True  # 标记有记录被删除
                else:  # 如果请求失败
                    self.log(f"Failed to fetch runs. Status code: {response.status_code}")  # 打印错误信息
                    break  # 退出循环

            if not any_deleted:  # 如果没有任何记录被删除，退出循环
                break

    def log(self, message):
        beijing_time = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8)))  # 获取北京时间
        current_time_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]  # 获取当前时间，精确到三位毫秒
        print(f"{current_time_str} {message}")  # 打印日志消息


if __name__ == "__main__":
    repository_name = os.environ.get("REPOSITORY_NAME")
    github_token = os.environ.get("GITHUB_TOKEN")
    hour_count = int(os.environ.get("HOUR_COUNT"))
    repo_url = f"https://api.github.com/repos/{repository_name}"  # GitHub仓库URL
    token = f"{github_token}"  # GitHub个人访问令牌

    manager = GitHubActionsManager(repo_url, token)  # 创建GitHubActionsManager实例
    manager.delete_old_runs()  # 删除指定小时前的运行记录
