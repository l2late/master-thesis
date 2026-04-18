%     Copyright (C) 2021, ETH Zurich [Dominic Liao-McPherson]
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

function [dx,y] = agent_dynamics(x,u,k)

  p = x(3);
  r = (x(1) - u(1))^2 + (x(2) - u(2))^2;
  r = sqrt(r);

  
  dx = zeros(3,1);

  v = k(1) * r * cos(p);
  w = -k(1)*sin(p)*cos(p) - k(2)*p;

  psi = atan2(x(2)-u(2),x(1)-u(1));
  dx(1) = v * cos(p + psi - pi);
  dx(2) = v * sin(p + psi - pi);
  dx(3) = - k(2)*p;

  y = x(1:2);
end
