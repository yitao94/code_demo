%% Verifying Two Methods from Fares and Yitao
%
% Because Fares and Yitao use slightly different methods in performing the
% strutures of 8*8 and 16*16 points DWHT, this .m file wants to verify
% whether they are both correct or not and compare which one of them can be
% better performed on FPGA hardware platform. 
%
% What's more, a combined method with Fares' and Yitao's is designed,
% which deletes the changed order of Fares' 8*8 64P2D DWHT function, then
% applies Yitao's order in 16*16 256P2D DWHT function.
%
% Fares Charfi   Matrikelnummer 03662038,
% Yitao Jin   Matrikelnummer 03680500,
%
% Function: DWHT_4P2D_lossless;
%           DWHT_64P2D;
%           DWHT_256P2D;
%           DWHT_64P2D_wo_change_output;
%           DWHT_256P2D_new_output_order;
%
% Conclusion: Both Fares' and Yitao's work are correct.
%
% Edited by Yitao Jin (yitao.jin@tum.de) on 09/26/2017

%% Generate an Initial Input Matrix
%
% We are only interested in 64-point and 256-point 2D DWHT structures, so
% our input matrices are 8*8 and 16*16 random interger numbers.
%
clc;
clear all;

M_8 = round(rand(8,8)*10);
M_16 = round(rand(16,16)*10);

%% Generate Sequency-Order Hadamard Matrix
%
% According to Fares' thesis (Page 14-16), we firstly generate Hadamard
% Matrix by formula, then transfer it to sequency-order (low-to-high)
% version for the sake of better physical sense.

% H_1
C_1 = [1,1;1,-1];
H_1 = 1.0/sqrt(2) .* C_1;

% H_2
C_2 = [C_1,C_1;C_1,-C_1];
H_2 = 1.0/sqrt(2*2) .* C_2;

% H_3
C_3 = [C_2,C_2;C_2,-C_2];
for i = 1:8
    d = 0;
    for j = 2:8
        if C_3(i,j) ~= C_3(i,j-1)
            d = d+1;
        end
    end
    n(i) = d;
end
m = [1 5 7 3 4 8 6 2];
C_3_Hada = C_3(m,:);
H_3 = 1.0/sqrt(2*2*2) .* C_3_Hada;

% H_4
C_4 = [C_3,C_3;C_3,-C_3];
for i = 1:16
    d = 0;
    for j = 2:16
        if C_4(i,j) ~= C_4(i,j-1)
            d = d+1;
        end
    end
    n(i) = d;
end
m = [1 9 13 5 7 15 11 3 4 12 16 8 6 14 10 2];
C_4_Hada = C_4(m,:);
H_4 = 1.0/sqrt(2*2*2*2) .* C_4_Hada;

%% Calculate Real Matrix
%
% Using formula:
% $$ Y = H * M * H' $$
% We can get the corresponding result of Real Matrix
%
Y_8 = H_3 * M_8 * H_3';
Y_16 = H_4 * M_16 * H_4';

%% Fares Charfi's Method 
%
% For Fares' work, we just call those functions with only one change from
% "DWHT_4P2D_withoutladder_floor" to "DWHT_4P2D_lossless", and keep all the
% others same.

% 8*8 64P2D DWHT
Matrix_fares_8 = DWHT_64P2D (M_8);

% 16*16 256P2D DWHT
Matrix_fares_16 = DWHT_256P2D (M_16);

%% Yitao Jin's Method 

% 8*8 64P2D DWHT
% 1st
for i=0:3
    for j=0:3
        Matrix_yitao_8(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(M_8(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_8 = Matrix_yitao_8(:,[1 3 2 4 5 7 6 8]);
Matrix_yitao_8 = Matrix_yitao_8([1 3 2 4 5 7 6 8],:); 

% 2nd
for i=0:3
    for j=0:3
        Matrix_yitao_8(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(Matrix_yitao_8(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_8 = Matrix_yitao_8(:,[1 5 3 7 2 6 4 8]);
Matrix_yitao_8 = Matrix_yitao_8([1 5 3 7 2 6 4 8],:);

% 3rd
for i=0:3
    for j=0:3
        Matrix_yitao_8(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(Matrix_yitao_8(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_8 = Matrix_yitao_8(:,[1 2 6 5 7 8 4 3]); % change the rows positions
Matrix_yitao_8 = Matrix_yitao_8([1 2 6 5 7 8 4 3],:); % change the columns positions

% 16*16 256P2D DWHT
% 1st
for i=0:7
    for j=0:7
        Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(M_16(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_16 = Matrix_yitao_16(:,[1 3 2 4 5 7 6 8 9 11 10 12 13 15 14 16]);
Matrix_yitao_16 = Matrix_yitao_16([1 3 2 4 5 7 6 8 9 11 10 12 13 15 14 16],:); 

% 2nd
for i=0:7
    for j=0:7
        Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_16 = Matrix_yitao_16(:,[1 5 3 7 2 6 4 8 9 13 11 15 10 14 12 16]);
Matrix_yitao_16 = Matrix_yitao_16([1 5 3 7 2 6 4 8 9 13 11 15 10 14 12 16],:);

% 3rd
for i=0:7
    for j=0:7
        Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_16 = Matrix_yitao_16(:,[1 9 3 11 5 13 7 15 2 10 4 12 6 14 8 16]); 
Matrix_yitao_16 = Matrix_yitao_16([1 9 3 11 5 13 7 15 2 10 4 12 6 14 8 16],:); 

% 4th
for i=0:7
    for j=0:7
        Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2) = DWHT_4P2D_lossless(Matrix_yitao_16(2*i+1:2*i+2,2*j+1:2*j+2)); 
    end
end
Matrix_yitao_16 = Matrix_yitao_16(:,[1 2 10 9 13 14 6 5 7 8 16 15 11 12 4 3]); 
Matrix_yitao_16 = Matrix_yitao_16([1 2 10 9 13 14 6 5 7 8 16 15 11 12 4 3],:); 

%% Combine Fares' and Yitao's Method
%
% We delete the changed order in Fares' 8*8 64P2D DWHT function, and use
% Yitao's order in new 16*16 256P2D DWHT function

% 16*16 256P2D DWHT
Matrix_fares_yitao_16 = DWHT_256P2D_new_output_order (M_16);

%% Verify

% Verify Yitao's Work

% 8*8 64P2D DWHT
Diff_jin_8 = Matrix_yitao_8 - Y_8;
max_Diff_jin_8 = max(abs(Diff_jin_8(:))) % the reason why it is not exactly zero is that the irrational number sqrt(8)

% 16*16 256P2D DWHT
Diff_jin_16 = Matrix_yitao_16 - Y_16;
max_Diff_jin_16 = max(abs(Diff_jin_16(:)))

% Verify Fares' Work

% 8*8 64P2D DWHT
Diff_fares_8 = Matrix_fares_8 - Y_8;
max_Diff_fares_8 = max(abs(Diff_fares_8(:)))

% 16*16 256P2D DWHT
Diff_fares_16 = Matrix_fares_16 - Y_16;
max_Diff_fares_16 = max(abs(Diff_fares_16(:)))

% Verify New Combined Method of Fares' and Yitao's
Diff_fares_yitao_16 = Matrix_fares_yitao_16 - Y_16;
max_Diff_fares_yitao_16 = max(abs(Diff_fares_yitao_16(:)))

% Compare Fares' and Yitao's Results Directly
Comp_F_J_8 = Matrix_fares_8 - Matrix_yitao_8    % Make subtraction
Comp_F_J_16 = Matrix_fares_16 - Matrix_yitao_16