import os
# from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
# from datetime import datetime, timedelta
# from airflow.operators.python_operator import PythonOperator
import pandas as pd
import torch
import cv2 as cv

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import paramiko
import os
import pytz
import time

import psycopg2
import platform
import pathlib

# Check the operating system and set the appropriate path type
if platform.system() == 'Windows':
    pathlib.PosixPath = pathlib.WindowsPath
else:
    pathlib.WindowsPath = pathlib.PosixPath

hostname = '172.30.81.141'  # เปลี่ยนเป็น IP ของ Raspberry Pi
port = 22
username = 'bross'  # เปลี่ยนเป็นชื่อผู้ใช้ของคุณ
password = '123456'  # หรือใช้ SSH Key
remote_path = '/home/bross/take_pic/img/'  # โฟลเดอร์ที่เก็บภาพบน Raspberry Pi
local_path = '/usr/local/spark/assets/img/'  # โฟลเดอร์ที่ต้องการเก็บภาพใน Airflow
now_7 = datetime.now(pytz.timezone('Asia/Bangkok'))
now = datetime.now()
###############################################
# Python Function
###############################################

def count_car(results):
    up_left = 0
    down_right = 0
    up_right = 0
    down_left = 0
    hfw = 640
    hrh = 320
    hlh = 245
    for i in results.xyxy[0].cpu():
        if i[0] > hfw and i[1] < hrh:
            up_right +=1
        elif i[0] > hfw and i[1] > hrh:
            down_right +=1
        elif i[0] < hfw and i[1] < hlh :
            up_left += 1
        elif i[0] < hfw and i[1] > hlh :
            down_left += 1 

    print(f'left up:{up_left} right up:{up_right}')
    print(f'left under:{down_left} right under:{down_right}')
    return up_left, up_right, down_left, down_right

def dag_2_postgre_sql(path_file, file_name, up_left, up_right, down_left, down_right):
    # pg_hook = PostgresHook(postgres_conn_id='172.30.88.24', schema='public')
    # connection = pg_hook.get_conn()
    # cursor = connection.cursor()

    conn = psycopg2.connect(
        host="172.30.81.47",
        database="aies_dashdb",
        user="coe",
        password="CoEpasswd",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO car (path, filename, top_left, top_right, down_left, down_right, created_date, updated_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", ("C:/Users/student/Desktop/6410110337/pipek/data/images/"+file_name, file_name, up_left, up_right, down_left, down_right, datetime.now(), datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def calculate_sales():
    os.makedirs(local_path, exist_ok=True)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password)
    sftp = ssh.open_sftp()
    time.sleep(10)
    try:
        files = sftp.listdir(remote_path)
        date = f"{now_7.year}-{now_7.month :02d}-{now_7.day :02d}-{now_7.hour :02d}-{now_7.minute :02d}.png"
        print(date)
        for file in files:
            if file.endswith('.png'):
                # if str(now_7.hour) == file[11:13] and str(now.minute) == file[14:16]:
                # print(f"kuy {file} {type(file)}")
                if date == file:
                    remote_file = os.path.join(remote_path, file)
                    local_file = os.path.join(local_path, file)
                    sftp.get(remote_file, local_file)
                    # print(f'get {file} keep {local_file}, {remote_file}')
                    img = cv.imread(local_file)
                    h, w, c = img.shape
                    img = img[int(h*0.29) : int(h*0.63)]
                    resize = cv.resize(img, (1280, 640), interpolation= cv.INTER_LINEAR)
                    model = torch.hub.load("/usr/local/spark/assets/yolov5", "custom", path="/usr/local/spark/assets/yolov5/best.pt", source='local', force_reload=True)
                    results = model(resize)
                    up_left, up_right, down_left, down_right = count_car(results)
                    print("KUY")
                    dag_2_postgre_sql(local_file, file, up_left, up_right, down_left, down_right)
                    print("KUY")

    except Exception as e:
        print(f'error at: {e}')
    finally:
        sftp.close()

###############################################
# DAG Definition
###############################################


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(now.year, now.month, now.day, minute=0),
    "email": ["airflow@airflow.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1)
}

dag = DAG(
    dag_id="bross-5-plush-model",
    description="call function python",
    default_args=default_args,
    schedule_interval=timedelta(minutes = 15)
)

start = DummyOperator(task_id="start", dag=dag)

python_job = PythonOperator(
    task_id="job",
    python_callable=calculate_sales,
    dag=dag)

end = DummyOperator(task_id="end", dag=dag)

start >> python_job >> end
# start >> end