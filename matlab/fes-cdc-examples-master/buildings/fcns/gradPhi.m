%     Copyright (C) 2021  Mathias Hudoba de Badyn
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.

function [gradPhi] = gradPhi(x,u,v,H,h,room_vec,dist_vec,A,B,Bvu,Bxu,xCon,eta)
%gradPhi

%Bvu should only be for measurable disturbances, i.e. ambient air temp
%going into the AHU. Everything else should be zeroed out. Dist_vec should
%contain the indices of the non-zero disturbances

v_old = v;
v = zeros(size(v));

for ii = 1:length(dist_vec)
    ind = dist_vec(ii);
    v(ind) = v_old(ind);
end

x_old = x;
x = zeros(size(x));
% same thing for x
for ii = 1:length(room_vec)
    ind = room_vec(ii);
    x(ind) = x_old(ind);
end


num_rooms = length(room_vec);

% get sizes of things
[nx] = length(x);
[nu] = length(u);
[nv] = length(v);

% get derivative of cost with respect to state
grad_x_C = zeros(nx,1);
for ii = 1:num_rooms
    ind = room_vec(ii);
    grad_x_C(ind) = eta*softThreshold(x(ind), xCon.T_min(ind), xCon.T_max(ind));    
end

% get sensitivity
grad_x_f = A;

for ii = 1:nu
    grad_x_f = grad_x_f + u(ii)*Bxu(:,:,ii);
end

bx_mat = zeros(size(B));
bv_mat = zeros(size(B));

for ii = 1:nu
    bx_mat(:,ii) = Bxu(:,:,ii)*x;
    bv_mat(:,ii) = Bvu(:,:,ii)*v;
end

grad_u_f = B + bx_mat + bv_mat;

grad_u_h = -inv(grad_x_f)*grad_u_f;

% get gradient of cost with respect to u

grad_u_C = H*u + h;

gradPhi = grad_u_C + grad_u_h'*grad_x_C;


end

