# audiobookshelf-provider-douban
audiobookshelf 豆瓣读书刮削

# 背景
本人一直在使用audiobookshelf听有声书，无奈这个应用给的刮削provider基本上无法刮削，也没有找到现成的刮削工具，所以自己写了一个。

# 官网文档
这个文档是audiobookshelf官方提供的provider定义的openapi规范。
```
https://github.com/advplyr/audiobookshelf/blob/master/custom-metadata-provider-specification.yaml
```
# 参考资料
基于下面其他大佬的源码改写
```
https://github.com/fugary/calibre-web-douban-api
```

# 如何使用
## 1.程序安装
```
# 所需环境 python 3.9+
# 安装python依赖
pip install -r requirements.txt
# 运行程序 默认端口 8000
python main.py
```
## 2.audiobookshelf使用
填写你的服务器地址，如：http://192.168.8.1:8000

# 当前现状&后续规划
## 现状
1、手工搜索可用，目前展示3个
2、自动刮削不可用，需要进一步研究audiobookshelf相关的配置

## 规划
1、稳定后会用env打包
2、同步打包docker镜像推送至dockerhub


