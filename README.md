1、查询雪球指定用户的自选股票 和 关注列表，保存在files下的stocksXX.json和watchlistXX.json文件中（本地运行保存在local_files目录下，github工作流定时运行保存在workflow_files目录下）
  第一次运行后，其他时间再次运行，可查看stocksXX_add.json 和 watchlistXX_add.json来获得该用户新增的自选股 和 新的关注人。

2、将需要查询的雪球用户【准确地】写入files目录下的cname.txt中，可以多个，换行分隔。

3、需要手动浏览器抓包获取自己的雪球token、自己用户uid，方法参考以下链接： http://blog.crackcreed.com/diy-xue-qiu-app-shu-ju-api/ 获取【xq_a_token】值和【u】值

4、如果拉取此仓库到本地电脑运行，可以直接在代码中利用set_xueqiu_token("xxxc", "xxxx")方法手动输入两值后即可运行。结果请在files——local_files目录下的json文件中查看

5、如果想利用github定时运行（每天上午10点），则：
 ①fork此项目，在自己项目页面Setting --Secrets and Variables--actions-New repository secret中， 添加：Name为 XQ_A_TOKEN，Secret为上方抓取到的【xq_a_token】值；继续添加Name为XQ_U，Secret为上方抓取到的【u】值。
 ②在自己项目页面Settings -> Actions -> General 里的Workflow permissions启用 “Read and Write permissions”并勾选： Allow GitHub Actions to create and approve pull requests
脚本每天每天上午10点自动运行，或者点击自己仓库的star也能手动运行。结果请在本github仓库代码中，files——workflow_files目录下的json文件中查看
（ps:每次提交github前，先从github拉取一次，获取最新的workflow产生的json文件。 ）

6、如果想将github定时运行结果推送至tg：需要仓库页面Setting --Secrets and Variables--actions-New repository secret中添加TG_BOT_TOKEN 和 TG_CHAT_ID。查看自己tg bot_token 和 chatid方法自行谷歌。
  如果想将结果github定时运行结果推送至微信：则Setting --Secrets and Variables--actions-New repository secret中添加PUSHPLUS_KEY。 获取pushplus token方法自行百度。
 PS:第一次运行时，不会推送add.json文件。之后每次运行，若该用户有新增的自选或关注，且不是一次新增大量关注，正常都会将新增部分内容（stockXX_add.json 和 watchlistXX_add.json）进行推送。