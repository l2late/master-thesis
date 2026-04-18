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

function [u] = getHysteresisRBS(room_vec, u_rad_vec, x, u, h_low, h_high, u_max, u_rbs_vec)
%getThermo: Safety-constrained excitation
% u_rbs_vec: Vector of RBS values for the radiators at this specific timestep

for ii = 1:length(room_vec)
    ind_u = u_rad_vec(ii);
    ind_r = room_vec(ii);
    
    % Get the pre-calculated random value for this specific room
    % (Assumes u_rbs_vec is ordered same as room_vec/u_rad_vec)
    val_rbs = u_rbs_vec(ii); 

    if x(ind_r) >= h_high
        u(ind_u) = 0;          % Safety High
    elseif x(ind_r) <= h_low
        u(ind_u) = u_max;      % Safety Low
    else
        u(ind_u) = val_rbs;    % Excitation
    end
end
end

