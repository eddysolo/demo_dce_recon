# fastMRI Breast: A publicly available radial k-space dataset of breast dynamic contrast-enhanced MRI

## Demonstration of DCE MRI reconstruction using temporal TV regularization
* Goal: 
        To make a publicly available radial k-space dataset of breast DCE-MRI which will promote development of fast and quantitative breast image reconstruction and machine learning methods.

* Code descripition: 

   **'loop_single_data.sh'** script executes two python scripts, `dce_recon.py` and `dcm_recon.py`. The scripts read k-space data from .h5 file stored within a patient folder (e.g., 'fastMRI_breast_003_2') and generate a new reconstructed image series based on user preferences (such as spokes per frame, slice index, and the number of slices). The resulting image series is stored in a new .h5 file ('_processed.h5') and in a DICOM folder ('_processed'), both saved under the patient folder.

* How to run on your local computer?

    To run the bash script **'loop_single_data.sh'** on your local computer, you need to firstly install the required python environments, which I suggest to use `conda`.

    Here are the steps:

    1. create a new `conda` environment in the terminal:

    ```bash
    conda create -n dce python=3.10
    conda activate dce
    which python  # to validate the python is under the environment
    ```

    ```bash
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
    ```

    2. clone and install `sigpy` in the terminal:

    ```bash
    git clone https://github.com/ZhengguoTan/sigpy.git
    cd sigpy
    pip install setuptools==58.2.0  # might be needed, try first without
    python -m pip install -e . 
    ```

    3. Now you should be able to run the script with four inputs: data, spokes per frame, slice index, number of slices

    ```bash
    bash loop_single_data.sh fastMRI_breast_002_1 72 100 10 
    ```
## fastMRI Breast dataset:
The data are available for free through: https://fastmri.med.nyu.edu/. After acceptance of the dataset sharing agreement, researchers receive an email containing links to download the data. In order to use an .h5 file with this code, save it inside a folder named with its patient code name (e.g., 'fastMRI_breast_003_2'), as instructed in 'Code description' above. Note that the provided DICOM files are in 4D (x,y,z,time) with 4 time frames. For easier viewing, we recommend using https://firevoxel.org/

Our dataset also includes case-level labels arranged in an excel file (also available here under 'breast_fastMRI_final') indicating patient age, menopause status, lesion status (negative, benign, and malignant), and lesion type for each case. 



## Citation: 
If you use the fastMRI DCE Breast data or code in your research, please cite the following arXiv paper: https://arxiv.org/abs/2406.05270

## References:

* Zhang S, Block KT, Frahm J. [Magnetic resonance imaging in real time: advances using radial FLASH](https://doi.org/10.1002/jmri.21987). J Magn Reson Imaging 2010;31:101-109.

* Uecker M, Zhang S, Voit D, Karaus A, Merboldt KD, Frahm J. [Real-time MRI at a resolution of 20 ms](https://doi.org/10.1002/nbm.1585). NMR Biomed 2010;23:986-994.

* Block KT, Chandarana H, Milla S, Bruno M, Mulholland T, Fatterpekar G, Hagiwara M, Grimm R, Geppert C, Kiefer B, Sodickson DK. [Towards routine clinical use of radial stack-of-stars 3D gradient-echo sequences for reducing motion sensitivity](https://doi.org/10.13104/jksmrm.2014.18.2.87). J Korean Magn Reson Med 2014;18:87-106.

* Feng L, Grimm R, Block KT, Chandarana H, Kim S, Xu J, Axel L, Sodickson DK, Otazo R. [Golden‐angle radial sparse parallel MRI: combination of compressed sensing, parallel imaging, and golden‐angle radial sampling for fast and flexible dynamic volumetric MRI](https://doi.org/10.1002/mrm.24980). Magn Reson Med 2014;72:707-717.
