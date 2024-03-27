import argparse
import h5py
import os
import pathlib

import numpy as np
import sigpy as sp
import torch
import cupy as cp

from sigpy.mri import app

DIR = os.path.dirname(os.path.realpath(__file__))

# %%
def get_traj(N_spokes=13, N_time=1, base_res=320, gind=1):

    N_tot_spokes = N_spokes * N_time

    N_samples = base_res * 2

    base_lin = np.arange(N_samples).reshape(1, -1) - base_res

    tau = 0.5 * (1 + 5**0.5)
    base_rad = np.pi / (gind + tau - 1)

    base_rot = np.arange(N_tot_spokes).reshape(-1, 1) * base_rad

    traj = np.zeros((N_tot_spokes, N_samples, 2))
    traj[..., 0] = np.cos(base_rot) @ base_lin
    traj[..., 1] = np.sin(base_rot) @ base_lin

    traj = traj / 2

    traj = traj.reshape(N_time, N_spokes, N_samples, 2)

    return np.squeeze(traj)

# %% compute coil sensitivity maps
def get_coil(ksp, device=sp.Device(-1)):

    N_coils, N_spokes, N_samples = ksp.shape

    base_res = N_samples // 2

    ishape = [N_coils] + [base_res] * 2

    traj = get_traj(N_spokes=N_spokes, N_time=1,
                    base_res=base_res, gind=1)

    dcf = (traj[..., 0]**2 + traj[..., 1]**2)**0.5

    F = sp.linop.NUFFT(ishape, traj)

    cim = F.H(ksp * dcf)
    cim = sp.fft(cim, axes=(-2, -1))

    mps = app.EspiritCalib(cim, device=device).run()
    return sp.to_device(mps)


# %%
if __name__ == "__main__":

    # %% parse
    parser = argparse.ArgumentParser(description='run dce reconstruction.')

    parser.add_argument('--dir', type=str,
                        default=DIR,
                        help='the directory where raw .h5 data is stored')

    parser.add_argument('--data',
                        default='Breast_seg1_CCCTrio#F374720.h5',
                        help='radial k-space data')

    parser.add_argument('--codedName',
                        default='fastMRI_breast_001_1.h5',
                        help='unique coded file name')

    parser.add_argument('--spokes_per_frame', type=int, default=12,
                        help='number of spokes per frame')

    parser.add_argument('--slice_idx', type=int, default=0,
                        help='which slice index for the reconstruction to begin with')

    parser.add_argument('--slice_inc', type=int, default=1,
                        help='number of slices to be reconstructed')

    parser.add_argument('--center_partition', type=int, default=31,
                        help='the center partition index [default: 31]')

    parser.add_argument('--images_per_slab', type=int, default=192,
                        help='total number of images per slab [default: 192]')

    args = parser.parse_args()

    device = sp.Device(0 if torch.cuda.is_available() else -1)
    print('> device ', device)

    OUT_DIR = DIR + '/' + args.codedName
    OUT_DIR = OUT_DIR.split('.h5')[0]
    pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    #print('> reconstructed files are stored in: ', OUT_DIR)

    # %% read in k-space data
    IN_DIR = args.dir + '/' + args.data
    print('> read in data ', IN_DIR)
    f = h5py.File(IN_DIR, 'r')
    ksp_f = f['kspace'][:].T
    print('> kspace shape ', ksp_f.shape)
    f.close()

    ksp = ksp_f[0] + 1j * ksp_f[1]
    ksp = np.transpose(ksp, (3, 2, 0, 1))

    # zero-fill the slice dimension
    partitions = ksp.shape[0]
    shift = int(args.images_per_slab / 2 - args.center_partition)

    ksp_zf = np.zeros_like(ksp, shape=[args.images_per_slab] + list(ksp.shape[1:]))
    ksp_zf[shift : shift + partitions, ...] = ksp

    ksp_zf = sp.fft(ksp_zf, axes=(0,))

    N_slices, N_coils, N_spokes, N_samples = ksp_zf.shape

    base_res = N_samples // 2

    N_time = N_spokes // args.spokes_per_frame

    N_spokes_prep = N_time * args.spokes_per_frame

    ksp_redu = ksp_zf[:, :, :N_spokes_prep, :]
    print('  ksp_redu shape: ', ksp_redu.shape)

    # %% retrospecitvely split spokes
    ksp_prep = np.swapaxes(ksp_redu, 0, 2)
    ksp_prep_shape = ksp_prep.shape
    ksp_prep = np.reshape(ksp_prep, [N_time, args.spokes_per_frame] + list(ksp_prep_shape[1:]))
    ksp_prep = np.transpose(ksp_prep, (3, 0, 2, 1, 4))
    ksp_prep = ksp_prep[:, :, None, :, None, :, :]
    print('  ksp_prep shape: ', ksp_prep.shape)

    # %% trajectories
    traj = get_traj(N_spokes=args.spokes_per_frame,
                    N_time=N_time, base_res=base_res,
                    gind=1)
    print('  traj shape: ', traj.shape)

    # %% slice-by-slice recon

    if args.slice_idx >= 0:
        slice_loop = range(args.slice_idx, args.slice_idx + args.slice_inc, 1)
    else:
        slice_loop = range(N_slices)

    acq_slices = []

    for s in slice_loop:
        print('>>> slice ', str(s).zfill(3))

        # coil sensitivity maps
        print('> compute coil sensitivity maps')
        C = get_coil(ksp_zf[s], device=device)
        C = C[:, None, :, :]
        print('  coil shape: ', C.shape)

        # recon
        k1 = ksp_prep[s]
        R1 = app.HighDimensionalRecon(k1, C,
                        combine_echo=False,
                        lamda=0.001,
                        coord=traj,
                        regu='TV', regu_axes=[0],
                        max_iter=10,
                        solver='ADMM', rho=0.1,
                        device=device,
                        show_pbar=False,
                        verbose=True).run()

        acq_slices.append(R1)

    acq_slices = sp.to_device(acq_slices)

    acq_slices = cp.array(acq_slices)
    acq_slices = cp.asnumpy(acq_slices)
    acq_slices = np.squeeze(abs(acq_slices))

    #acq_slices = np.array(acq_slices)
    #print('> acq_slices shape: ', acq_slices.shape)

    # save recon files
    #f = h5py.File(OUT_DIR + '/reco_spokes' + str(args.spokes_per_frame).zfill(2) + '.h5', 'w')
    f = h5py.File(OUT_DIR + '/' + args.codedName + '.h5', 'w')

    dset = f.create_dataset('kspace', data=ksp_f)
    dset.attrs['partitions'] = '83'
    dset.attrs['centerPartition'] = '32'
    dset.attrs['imagesPerSlab'] = '192'

    dset = f.create_dataset('temptv', data=acq_slices)
    dset.attrs['spokes_per_frame'] = args.spokes_per_frame
    dset.attrs['images_per_slab'] = args.images_per_slab
    dset.attrs['frameNumber'] = N_time

    f.close()
