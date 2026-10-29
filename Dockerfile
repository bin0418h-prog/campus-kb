FROM python:3.13-slim

WORKDIR /app

# 国内服务器直连 PyPI 慢，默认走阿里云公网镜像；
# 阿里云 ECS 上可用内网镜像加速：
#   --build-arg PIP_INDEX_URL=http://mirrors.cloud.aliyuncs.com/pypi/simple/ \
#   --build-arg PIP_TRUSTED_HOST=mirrors.cloud.aliyuncs.com
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=
COPY requirements.txt .
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} ${PIP_TRUSTED_HOST:+--trusted-host ${PIP_TRUSTED_HOST}} -r requirements.txt

COPY app ./app
COPY static ./static

RUN mkdir -p uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
