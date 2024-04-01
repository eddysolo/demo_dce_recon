conda create -n dce python=3.10
conda activate dce
which python  # to validate the python is under the environment

conda install -c anaconda pip
python -m pip install torch torchvision torchaudio
python -m pip install tqdm
python -m pip install pydicom
python -m pip install numba
python -m pip install scipy
python -m pip install pywavelets
python -m pip install h5py
python -m pip install matplotlib

conda install -c conda-forge cupy cudnn cutensor nccl  # if you have GPU
conda install -c conda-forge numpy=1.24


sudo git clone https://github.com/ZhengguoTan/sigpy.git
cd sigpy
pip install setuptools==58.2.0
python -m pip install -e . 

sudo git clone https://github.com/eddysolo/demo_dce_recon.git
cd demo_dce_recon/


