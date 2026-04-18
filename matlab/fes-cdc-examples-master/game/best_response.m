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

function u = best_response(ubar,y,i,c,umax,umin);

  [nu,N] = size(y);
  
  H = (1 + c*(N-1))*eye(nu);


  f = -ubar;


  for j = 1:N
    if i ~= j
      f = f - c*y(:,j);
    end
  end

  u = zeros(size(ubar));
  % opts = optimoptions('quadprog','display','off');
  % opts = optimoptions('quadprog');
  opts = optimoptions('quadprog','algorithm','active-set','display','off');
  u = quadprog(H,f,[],[],[],[],umin,umax,ubar,opts);
end

