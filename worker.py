# worker.py
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from search_engines import (
    get_google_search_results,
    get_bing_search_results,
    get_baidu_search_results
)
from utils import save_results_to_txt


class Worker(QObject):
    """
    工作线程，用于执行搜索任务。
    """
    finished = pyqtSignal(list, str)  # 发送结果和文件路径
    error = pyqtSignal(str)

    def __init__(self, queries, num_results=5, engine='Google', custom_question=None):
        super().__init__()
        self.queries = queries  # 接受多个关键词
        self.num_results = num_results
        self.engine = engine  # 搜索引擎
        self.custom_question = custom_question  # 自定义问题
        self._is_running = True  # 添加运行状态标志

    @property
    def is_running(self):
        return self._is_running

    def stop(self):
        """
        停止工作线程。
        """
        self._is_running = False

    def run(self):
        """
        执行搜索任务。
        """
        try:
            all_results = []
            logging.info(
                f"工作线程开始执行搜索任务，关键词: {self.queries}, "
                f"结果数量: {self.num_results}, 搜索引擎: {self.engine}"
            )
            for query in self.queries:
                if not self.is_running:
                    logging.info("搜索任务被中断。")
                    break
                if self.engine == 'Google':
                    results = get_google_search_results(
                        query, self.num_results, self
                    )
                elif self.engine == 'Bing':
                    results = get_bing_search_results(
                        query, self.num_results, self
                    )
                elif self.engine == '百度':
                    results = get_baidu_search_results(
                        query, self.num_results, self
                    )
                else:
                    raise Exception("不支持的搜索引擎。")
                # 添加查询词到结果中
                for result in results:
                    result['query'] = query
                all_results.append(results)

            if not self.is_running:
                logging.info("搜索任务已被用户中断，停止后续操作。")
                return

            # 展平结果列表
            flat_results = [item for sublist in all_results for item in sublist]

            filename = save_results_to_txt(
                flat_results,
                ', '.join(self.queries),
                engine=self.engine,
                custom_question=self.custom_question
            )
            self.finished.emit(flat_results, filename)
            logging.info("工作线程搜索任务完成。")
        except Exception as e:
            self.error.emit(str(e))
            logging.error(f"工作线程搜索任务失败：{e}")