echo "Looking for the enviornment file of env $1"
conda env list | grep $1 >> /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Environment exists: Skipping Creation"
else
    echo "Environment does not exist: Creating"
    conda create -n $1 python=3.9 ipython pip
    echo "Environment $1 created"
fi

conda activate $1
#Installing PIP packages from requirements.txt
echo "Installing PIP packages from requirements.txt"
pip install -r requirements.txt

echo "Environment $1 is ready to use"