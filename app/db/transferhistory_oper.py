import time
from typing import Any, List, Optional

from app.core.context import MediaInfo
from app.core.meta import MetaBase
from app.db import DbOper
from app.db.models.transferhistory import TransferHistory
from app.schemas import TransferInfo, FileItem


class TransferHistoryOper(DbOper):
    """
    转移历史管理
    """

    def get(self, historyid: int) -> TransferHistory:
        """
        获取转移历史
        :param historyid: 转移历史id
        """
        return TransferHistory.get(self._db, historyid)

    def get_by_title(self, title: str) -> List[TransferHistory]:
        """
        按标题查询转移记录
        :param title: 数据key
        """
        return TransferHistory.list_by_title(self._db, title)

    def get_by_src(self, src: str, storage: Optional[str] = None) -> TransferHistory:
        """
        按源查询转移记录
        :param src: 数据key
        :param storage: 存储类型
        """
        return TransferHistory.get_by_src(self._db, src, storage)

    def get_by_dest(self, dest: str) -> TransferHistory:
        """
        按转移路径查询转移记录
        :param dest: 数据key
        """
        return TransferHistory.get_by_dest(self._db, dest)

    def list_by_hash(self, download_hash: str) -> List[TransferHistory]:
        """
        按种子hash查询转移记录
        :param download_hash: 种子hash
        """
        return TransferHistory.list_by_hash(self._db, download_hash)

    def add(self, **kwargs):
        """
        新增转移历史
        """
        kwargs.update({
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        TransferHistory(**kwargs).create(self._db)

    def statistic(self, days: Optional[int] = 7) -> List[Any]:
        """
        统计最近days天的下载历史数量
        """
        return TransferHistory.statistic(self._db, days)

    def get_by(self, title: Optional[str] = None, year: Optional[str] = None, mtype: Optional[str] = None,
               season: Optional[str] = None, episode: Optional[str] = None, tmdbid: Optional[int] = None,
               dest: Optional[str] = None) -> List[TransferHistory]:
        """
        按类型、标题、年份、季集查询转移记录
        """
        return TransferHistory.list_by(db=self._db,
                                       mtype=mtype,
                                       title=title,
                                       dest=dest,
                                       year=year,
                                       season=season,
                                       episode=episode,
                                       tmdbid=tmdbid)

    def get_by_type_tmdbid(self, mtype: Optional[str] = None, tmdbid: Optional[int] = None) -> TransferHistory:
        """
        按类型、tmdb查询转移记录
        """
        return TransferHistory.get_by_type_tmdbid(db=self._db,
                                                  mtype=mtype,
                                                  tmdbid=tmdbid)

    def delete(self, historyid):
        """
        删除转移记录
        """
        TransferHistory.delete(self._db, historyid)

    def truncate(self):
        """
        清空转移记录
        """
        TransferHistory.truncate(self._db)

    def add_force(self, **kwargs) -> TransferHistory:
        """
        新增转移历史，相同源目录的记录会被删除
        """
        if kwargs.get("src"):
            transferhistory = TransferHistory.get_by_src(self._db, kwargs.get("src"))
            if transferhistory:
                transferhistory.delete(self._db, transferhistory.id)
        kwargs.update({
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        TransferHistory(**kwargs).create(self._db)
        return TransferHistory.get_by_src(self._db, kwargs.get("src"))

    def update_download_hash(self, historyid, download_hash):
        """
        补充转移记录download_hash
        """
        TransferHistory.update_download_hash(self._db, historyid, download_hash)

    def add_success(self, fileitem: FileItem, mode: str, meta: MetaBase,
                    mediainfo: MediaInfo, transferinfo: TransferInfo,
                    downloader: Optional[str] = None, download_hash: Optional[str] = None):
        """
        新增转移成功历史记录
        """
        self.add_force(
            src=fileitem.path,
            src_storage=fileitem.storage,
            src_fileitem=fileitem.dict(),
            dest=transferinfo.target_item.path if transferinfo.target_item else None,
            dest_storage=transferinfo.target_item.storage if transferinfo.target_item else None,
            dest_fileitem=transferinfo.target_item.dict() if transferinfo.target_item else None,
            mode=mode,
            type=mediainfo.type.value,
            category=mediainfo.category,
            title=mediainfo.title,
            year=mediainfo.year,
            tmdbid=mediainfo.tmdb_id,
            imdbid=mediainfo.imdb_id,
            tvdbid=mediainfo.tvdb_id,
            doubanid=mediainfo.douban_id,
            seasons=meta.season,
            episodes=meta.episode,
            image=mediainfo.get_poster_image(),
            downloader=downloader,
            download_hash=download_hash,
            status=1,
            files=transferinfo.file_list
        )

    def add_fail(self, fileitem: FileItem, mode: str, meta: MetaBase, mediainfo: MediaInfo = None,
                 transferinfo: TransferInfo = None, downloader: Optional[str] = None, download_hash: Optional[str] = None):
        """
        新增转移失败历史记录
        """
        if mediainfo and transferinfo:
            his = self.add_force(
                src=fileitem.path,
                src_storage=fileitem.storage,
                src_fileitem=fileitem.dict(),
                dest=transferinfo.target_item.path if transferinfo.target_item else None,
                dest_storage=transferinfo.target_item.storage if transferinfo.target_item else None,
                dest_fileitem=transferinfo.target_item.dict() if transferinfo.target_item else None,
                mode=mode,
                type=mediainfo.type.value,
                category=mediainfo.category,
                title=mediainfo.title or meta.name,
                year=mediainfo.year or meta.year,
                tmdbid=mediainfo.tmdb_id,
                imdbid=mediainfo.imdb_id,
                tvdbid=mediainfo.tvdb_id,
                doubanid=mediainfo.douban_id,
                seasons=meta.season,
                episodes=meta.episode,
                image=mediainfo.get_poster_image(),
                downloader=downloader,
                download_hash=download_hash,
                episode_group=mediainfo.episode_group,
                status=0,
                errmsg=transferinfo.message or '未知错误',
                files=transferinfo.file_list
            )
        else:
            his = self.add_force(
                title=meta.name,
                year=meta.year,
                src=fileitem.path,
                src_storage=fileitem.storage,
                src_fileitem=fileitem.dict(),
                mode=mode,
                seasons=meta.season,
                episodes=meta.episode,
                downloader=downloader,
                download_hash=download_hash,
                status=0,
                errmsg="未识别到媒体信息"
            )
        return his

    def list_by_date(self, date: str) -> List[TransferHistory]:
        """
        查询某时间之后的转移历史
        :param date: 日期
        """
        return TransferHistory.list_by_date(self._db, date)
