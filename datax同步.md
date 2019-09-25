# datax同步数据

 作者：冥王

参考资料：https://github.com/alibaba/DataX

说明：表的字段 ，所有表都是JSID为增量的。以数据库中SecuMain表为例



## 网上直接下载datax 工具包

```
$ cd  {YOUR_DATAX_HOME}/bin
$ python datax.py {YOUR_JOB.json}
```

本次数据是从mysql同步到sqlserver

### 全量同步

secumain.json 文件如下编辑

```json

{
	"job": {
		"setting": {
			"speed": {
				"channel": 3
			},
			"errorLimit": {
				"record": 0,
				"percentage": 0.02
			}
		},
		"content": [{
			"reader": {
				"name": "mysqlreader",
				"parameter": {
					"username": "root",
					"password": "qfx@123456",
					"column": ["*"],
                                        "splitPk": "JSID",
					"connection": [{
                        "querySql": [
                             "select * from SecuMain where 1=1;"
                                                ],

						"jdbcUrl": [
							"jdbc:mysql://172.18.44.86:3306/jydb?useUnicode=true&characterEncoding=utf8"
						]
					}]
				}
			},
			"writer": {
				"name": "sqlserverwriter",
				"parameter": {
					"username": "HX_JYDB",
					"password": "HX@123456",
					"column": ["*"],
					"connection": [{
						"table": [
							"secumain"
						],
						"jdbcUrl":                                           "jdbc:sqlserver://120.27.217.112:1433;DatabaseName=HX_JYDB"
					}],
					"preSql": [
                                            "TRUNCATE TABLE @table"
					],
					"postSql": [
					]
				}
			}
		}]
	}
}

```



#### 运行一下命令

```shell
python datax.py secumain.json
```

### 增量同步

获取JSID的最大值写入文本

maxsecumain.json

```json
{
	"job": {
		"setting": {
			"speed": {
				"channel": 3
			},
			"errorLimit": {
				"record": 0,
				"percentage": 0.02
			}
		},
		"content": [{
			"reader": {
				"name": "sqlserverreader",
				"parameter": {
					"username": "HX_JYDB",
					"password": "HX@123456",
					"connection": [{
						"jdbcUrl": [
							"jdbc:sqlserver://120.27.217.112:1433;DatabaseName=HX_JYDB"
						],
						"querySql": [
							"SELECT max(jsid) FROM secumain;"
						]
					}]
				}
			},

			"writer": {
				"name": "txtfilewriter",
				"parameter": {
					"dateFormat": "yyyy-MM-dd HH:mm:ss",
					"fileName": "secumain",
					"fileFormat": "csv",
					"path": "/root/datax/bin/scripts/",
					"writeMode": "truncate"

				}
			}
		}]
	}

}

```

编写脚本

```shell

#!/bin/bash
### every exit != 0 fails the script
set -e

# 获取目标数据库最大jsid，并写入一个 csv 文件
python datax.py  maxsecumain.json
if [ $? -ne 0 ]; then
  echo "secumain_sync.sh error, can not get max_jsid from target db!"
  exit 1
fi
# 找到 DataX 写入的文本文件，并将内容读取到一个变量中
RESULT_FILE=`ls scripts/secumain*`
maxjsid=`cat $RESULT_FILE`
# 如果最大jsid不为 null 的话， 修改全部同步的配置，进行增量更新；
if [ "$maxjsid" != "null" ]; then
  # 设置增量更新过滤条件
  WHERE="jsid > '$maxjsid'"
  sed "s/1=1/$WHERE/g" secumain.json > secumain_tmp.json
  # 将第 45 行的 truncate 语句删除；
  sed '45d' secumain_tmp.json > secumain_inc.json
  # 增量更新
 python datax.py   secumain_inc.json
  # 删除临时文件
  rm ./secumain_tmp.json ./secumain_inc.json
else
  # 全部更新
 python datax.py    tables/secumain.json
fi

```

运行脚本 实现增量拷贝

```shell
sh secumain.sh 
```

