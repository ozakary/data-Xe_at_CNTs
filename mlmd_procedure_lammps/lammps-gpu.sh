#!/bin/bash -l
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-task=7
#SBATCH --time=48:00:00
#SBATCH --account=project_462001159
#SBATCH --output=test_symmetrix_%j.out
#SBATCH --error=test_symmetrix_%j.err

ml LUMI
ml partition/G
ml PrgEnv-amd
ml rocm
ml cray-fftw

export MPICH_GPU_SUPPORT_ENABLED=1
export MPICH_SMP_SINGLE_COPY_MODE=NONE
export OMP_NUM_THREADS=1
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

SYMMETRIX_BASE=/scratch/project_462001159/zakaryou/packages/lammps-symmetrix-build

export LD_LIBRARY_PATH=$SYMMETRIX_BASE/lib64:$SYMMETRIX_BASE/lib:$LD_LIBRARY_PATH

srun --ntasks=8 --gpus-per-task=1 --gpu-bind=closest \
  $SYMMETRIX_BASE/bin/lmp \
  -in xe_cnt_lammps.in \
  -k on g 1 \
  -sf kk \
  -pk kokkos newton on neigh half

ulimit -c 0
