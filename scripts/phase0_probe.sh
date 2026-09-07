#!/usr/bin/env bash
# ============================================================
# Phase 0 环境探测脚本（只读，不修改任何配置）
# 用法：
#   1. 把本脚本拷贝到 VM 的 /tmp/ 目录
#   2. 在三台机器上分别执行：bash /tmp/phase0_probe.sh
#   3. 把输出（尤其 hadoop102 的）完整贴回给 AI
# 注意：脚本只做读取/查询，不会改集群任何配置或数据。
# ============================================================
set -u
# 预初始化，避免 set -u 在未找到配置时直接退出
hive_conf=""
hms_url=""
mysql_host=""
mysql_port="3306"

echo "============================================================="
echo "[VM] hostname: $(hostname)"
echo "[VM] IP: $(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^(192\.168\.|10\.|172\.)' | head -1)"
echo "[VM] OS: $(sed -n 's/^PRETTY_NAME="\?\(.*\)"\?$/\1/p' /etc/os-release 2>/dev/null | tr -d '"')"
echo "[VM] 内存: $(free -h | awk '/Mem:/{print $2" 总量 / "$7" 可用"}')"
echo "[VM] CPU 核数: $(nproc)"
echo "[VM] 本机时区: $(date +%Z' '%z)"
echo "============================================================="

echo "--- 组件版本 ---"
for cmd in "hadoop version" "hive --version" "spark-submit --version" \
           "flume-ng version" "sqoop version"; do
  bin=${cmd%% *}
  if command -v "$bin" >/dev/null 2>&1; then
    echo "[VER] $cmd => $($cmd 2>&1 | grep -iE '[0-9]+\.[0-9]+' | head -1)"
  else
    echo "[VER] $bin: 命令不存在"
  fi
done
# ZooKeeper 版本（zkServer.sh 无 version 子命令，从 jar 文件名取）
zk_jar=$(find /opt/module /opt/soft /usr/local /opt/install -maxdepth 3 -name "zookeeper-*.jar" 2>/dev/null | grep -v sources | head -1)
echo "[VER] zookeeper: $(basename "$zk_jar" 2>/dev/null | sed 's/zookeeper-\(.*\)\.jar/\1/')"
# Kafka 版本（kafka-topics.sh --version 自 Kafka 2.x 起支持）
if command -v kafka-topics.sh >/dev/null 2>&1; then
  echo "[VER] kafka: $(kafka-topics.sh --version 2>&1 | tail -1)"
else
  echo "[VER] kafka: kafka-topics.sh 不在 PATH（可能未配置环境变量，需查安装目录）"
fi
# DataX 版本（安装目录）
datax_home=$(ls -d /opt/module/datax /opt/soft/datax /opt/install/datax /usr/local/datax 2>/dev/null | head -1)
if [ -n "$datax_home" ]; then
  echo "[VER] DataX: $datax_home（reader 插件数 $(ls "$datax_home"/plugin/reader 2>/dev/null | wc -l)）"
else
  echo "[VER] DataX: 未在常见路径找到，跳过"
fi
# DolphinScheduler 版本（从 api jar 文件名取）
ds_home=$(ls -d /opt/module/dolphinscheduler* /opt/soft/dolphinscheduler* /opt/install/dolphinscheduler* /usr/local/dolphinscheduler* 2>/dev/null | head -1)
ds_jar=$(find "${ds_home:-/opt/module}" /opt/soft -maxdepth 3 -name "dolphinscheduler-api-*.jar" 2>/dev/null | head -1)
echo "[VER] DolphinScheduler: 安装目录 ${ds_home:-未找到}，api jar $(basename "$ds_jar" 2>/dev/null)"
echo "[VER] DolphinScheduler 进程: $(ps -ef | grep -i dolphinscheduler | grep -v grep | awk '{print $8" "$9}' | head -3 | tr '\n' ' ')"
# Superset 版本
if command -v superset >/dev/null 2>&1; then
  echo "[VER] superset: $(superset version 2>&1 | head -1)"
else
  echo "[VER] superset: 命令不存在"
fi

echo "--- 关键端口监听（ss -tln；root 下额外显示进程） ---"
ss_cmd="ss -tln"
[ "$(id -u)" = "0" ] && ss_cmd="ss -tlnp"
for port in 8020 9000 9864 9083 10000 10001 10002 3306 12345 5176 8888 8088 2181 9092; do
  line=$($ss_cmd 2>/dev/null | grep ":$port ")
  if [ -n "$line" ]; then
    echo "[PORT] $port: $line"
  else
    echo "[PORT] $port: 无监听"
  fi
done

echo "--- 网络模式判断（多网卡/网关信息） ---"
ip -4 addr show | grep -E "inet |^[0-9]+:" | head -20
echo "[GW] 默认路由: $(ip route 2>/dev/null | grep default)"

echo "--- Hive 配置定位（hive-site.xml） ---"
prop_val() {
  # 提取 hive-site.xml 中 <name>xxx</name> 对应的 <value>
  grep -A1 "<name>$1</name>" "$hive_conf" 2>/dev/null | grep -o '<value>[^<]*' | head -1 | sed 's/<value>//'
}
hive_conf=$(find /opt/module/hive /opt/soft/hive /opt/install/hive /usr/local/hive /etc/hive /opt/installs/hive -name hive-site.xml 2>/dev/null | head -1)
if [ -n "$hive_conf" ]; then
  echo "[HIVE] hive-site.xml: $hive_conf"
  hms_url=$(prop_val "javax.jdo.option.ConnectionURL")
  echo "[HIVE] ConnectionURL: $hms_url"
  echo "[HIVE] ConnectionUserName: $(prop_val "javax.jdo.option.ConnectionUserName")"
  echo "[HIVE] HS2 端口: $(prop_val "hive.server2.thrift.port")"
  echo "[HIVE] HS2 host 绑定: $(prop_val "hive.server2.thrift.bind.host")"
  echo "[HIVE] metastore uris: $(prop_val "hive.metastore.uris")"
  if [ -n "$hms_url" ]; then
    mysql_host=$(echo "$hms_url" | sed -E 's#jdbc:mysql://([^:/]+).*#\1#')
    mysql_port=$(echo "$hms_url" | sed -nE 's#jdbc:mysql://[^:]+:([0-9]+).*#\1#p')
    mysql_port="${mysql_port:-3306}"
    echo "[HMS] MySQL 主机: $mysql_host（IPv4: $(getent ahostsv4 "$mysql_host" | awk 'NR==1{print $1}')）  端口: ${mysql_port}"
    echo "[HMS] 提示: Windows 侧能否远程连此库将在宿主机另行测试；账号密码请人工确认（勿写入本文件）"
  fi
else
  echo "[HIVE] 未找到 hive-site.xml，请手动执行：find / -name hive-site.xml 2>/dev/null"
fi

echo "--- Spark Thrift Server 是否存在 ---"
echo "[SPARK] STS 进程: $(ps -ef | grep -iE 'thriftserver' | grep -v grep | head -2 | tr '\n' ' ')"
echo "[SPARK] Livy 进程: $(ps -ef | grep -iE 'livy' | grep -v grep | head -2 | tr '\n' ' ')"

echo "--- DolphinScheduler 认证方式探测（GET 默认接口，看返回码） ---"
curl -s -o /dev/null -w "[DS] http://localhost:12345/dolphinscheduler 返回 HTTP %{http_code}\n" \
  http://localhost:12345/dolphinscheduler 2>/dev/null || echo "[DS] 12345 端口不通"

echo "============================================================="
echo "[DONE] 探测完成。请把以上完整输出贴回给 AI。"
