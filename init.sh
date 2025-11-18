sudo apt-get update -y
sudo apt-get install -y cuda-12-2

export PATH=$(echo $PATH | tr ':' '\n' | grep -v cuda | tr '\n' ':' | sed 's/:$//')
export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH 2>/dev/null | tr ':' '\n' | grep -v cuda | tr '\n' ':' | sed 's/:$//')

export PATH=/usr/local/cuda-12.2/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH

uv sync


curl --progress-bar -L dl.min.io/aistor/minio/release/linux-amd64/minio.deb -o minio.deb
sudo dpkg -i minio.deb

sudo mkdir -p /usr/local/share/minio
sudo mkdir -p /etc/minio
sudo mkdir -p /var/minio
