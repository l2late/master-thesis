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

function [cost,u_cost] = getCumCost(H,cu,eta,x_array,u_array,xcon_array_min, xcon_array_max, t_space,room_vec)
%getCumCost: outputs total cost

cost = 0;
u_cost = 0;

dt = t_space(2)-t_space(1);

cost_array = zeros(length(t_space),1);
ucost_array = zeros(size(cost_array));

for ii = 1:length(t_space)
    
    u = u_array(:,ii);
    x = x_array(:,ii);
    tMin = xcon_array_min(ii);
    tMax = xcon_array_max(ii);
    
    cost_array(ii) =  0.5*u'*H*u + cu'*u + xCost(eta,tMin,tMax,x,room_vec);
    ucost_array(ii) = cu'*u;
end

int_cost = cumtrapz(t_space, cost_array);
int_u_cost = cumtrapz(t_space, ucost_array);

cost = int_cost(end);
u_cost = int_u_cost(end);


end

