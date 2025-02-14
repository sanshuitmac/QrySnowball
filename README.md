1、查询雪球指定用户的自选股票 和 关注列表。运行成功后结果将保存在files的文件里 2、将需要查询的雪球用户【准确地】写入files目录下的cname.txt中，可以多个，换行分隔。 3、需要手动浏览器抓包获取自己的雪球token、自己用户uid，方法参考以下链接： http://blog.crackcreed.com/diy-xue-qiu-app-shu-ju-api/ 获取xq_a_token值和u值

4、提取后，如果拉取此仓库到本地电脑运行，可以直接在代码中利用set_xueqiu_token("xxxc", "xxxx")方法手动输入两值后即可运行；
