## Python获取免费代理Ip

### 从一些网站爬取免费代理
* [https://cn-proxy.com/](https://cn-proxy.com/)

* [http://ip.jiangxianli.com/](http://ip.jiangxianli.com/)

* [http://31f.cn/http-proxy/](http://31f.cn/http-proxy/)

* [https://www.xicidaili.com/nn](https://www.xicidaili.com/nn)

## 使用说明

使用全部代理类
> proxy = AllProxy()
> proxy.run("https://movie.douban.com") # https://movie.douban.com用于检测ip对目标网站的连通性和有效性(该ip是否被封)
> proxy.links() # 全部有效的ip Link对象(host, port, schema, value)

使用单个代理类
> proxy = CNProxy()
> proxy.run("https://movie.douban.com")
> proxy.links()
> proxy.schedule() # 定期更新 重新获取最新的ip