# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 12:42:18 2019

@author: DHRUV BHATNAGAR
"""

import qkd_bb84_base as bb
import qkd_experiment_base as expt
import numpy as np
import random

XZ = np.array([[0.0, -1.0],
               [1.0,  0.0]])

class noisy_alice_con(bb.alice_con):
    
    def __init__(self, s_length, P_H_FAIL):
        super().__init__(s_length)
        self.P_H_FAIL = P_H_FAIL
    
    def hadamard_alice(self, states):
        # Works on a 2 x m matrix of qubits: each column independently fails
        # with probability P_H_FAIL, in which case X is applied instead of H.
        k = 1.0/np.sqrt(2.0)
        H = np.array([[k,k],[k,(-1*k)]])
        X = np.array([[0.0,1.0],[1.0, 0.0]])
        out = H @ states
        fail = np.random.uniform(0.0, 1.0, size=states.shape[1]) <= self.P_H_FAIL
        out[:, fail] = X @ states[:, fail]
        return out

class noisy_bob_con(bb.bob_con):
    
    def __init__(self, s_length, P_H_FAIL):
        super().__init__(s_length)
        self.P_H_FAIL = P_H_FAIL
    
    def hadamard_bob(self, states):
        # Works on a 2 x m matrix of qubits: each column independently fails
        # with probability P_H_FAIL, in which case X is applied instead of H.
        k = 1.0/np.sqrt(2.0)
        H = np.array([[k,k],[k,(-1*k)]])
        X = np.array([[0.0,1.0],[1.0, 0.0]])
        out = H @ states
        fail = np.random.uniform(0.0, 1.0, size=states.shape[1]) <= self.P_H_FAIL
        out[:, fail] = X @ states[:, fail]
        return out


class noisy_q_channel(bb.q_channel):
    
    def corrupt_state(self):
        self.temp_st_mtx = self.st_mtx_in
        self.length = np.shape(self.temp_st_mtx[0])[0] 
        inj_error_rate = 0.15*(1 + np.random.uniform(-0.25,0.25))
        self.cor = random.sample(range(self.length), np.floor(inj_error_rate*self.length).astype(int))
        self.temp_st_mtx[:, self.cor] = XZ @ self.temp_st_mtx[:, self.cor]  # Y error (up to global phase)
            
        self.out_st_mtx = self.temp_st_mtx        

#Modified subclass noisy_q_channel to accept variable error rate (0.00 to 1.00)
class variable_noisy_q_channel(noisy_q_channel):
    def __init__(self, error_rate):
        self.error_rate = error_rate

    def corrupt_state(self):
        self.temp_st_mtx = self.st_mtx_in
        self.length = np.shape(self.temp_st_mtx[0])[0] 
        inj_error_rate = self.error_rate*(1 + np.random.uniform(-0.25,0.25))
        self.cor = random.sample(range(self.length), np.floor(inj_error_rate*self.length).astype(int))
        self.temp_st_mtx[:, self.cor] = XZ @ self.temp_st_mtx[:, self.cor]  # Y error (up to global phase)
            
        self.out_st_mtx = self.temp_st_mtx

class noisy_qkd_experiment(expt.qkd_experiment):
    
    def __init__(self, SIZE_TX, P_H_FAIL):
        super().__init__(SIZE_TX)
        self.P_H_FAIL = P_H_FAIL
    
    def build_phase(self):
        super().build_phase()
        q_c_n = noisy_q_channel()
        a0_n = noisy_alice_con(self.SIZE_TX, self.P_H_FAIL)
        b0_n = noisy_bob_con(self.SIZE_TX, self.P_H_FAIL)
        
        # Polymorphism!
        self.q_c = q_c_n
        self.a0 = a0_n
        self.b0 = b0_n
        
def main():
    
    SIZE_TX = 1000
    P_H_FAIL = 0.05
    e1 = noisy_qkd_experiment(SIZE_TX, P_H_FAIL)
    e1.execute()
    

if __name__ == '__main__':
    main()
