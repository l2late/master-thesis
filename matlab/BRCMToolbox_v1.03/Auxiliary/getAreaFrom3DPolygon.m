


function A = getAreaFrom3DPolygon(vertices)
   % GETAREAFROM3DPOLYGON Returns the area of a polygon in 3D. Checks if all vertices lie in a plane.
   % ------------------------------------------------------------------------
   % This file is part of the BRCM Toolbox v1.03.
   %
   % The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
   % Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
   % 
   % The BRCM Toolbox is free software; you can redistribute it and/or modify
   % it under the terms of the GNU General Public License as published by
   % the Free Software Foundation, either version 3 of the License, or
   % (at your option) any later version.
   % 
   % The BRCM Toolbox is distributed in the hope that it will be useful,
   % but WITHOUT ANY WARRANTY; without even the implied warranty of
   % MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   % GNU General Public License for more details.
   % 
   % You should have received a copy of the GNU General Public License
   % along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
   %
   % For support check www.brcm.ethz.ch.
   % ------------------------------------------------------------------------
   
   
   
   no_vertices = length(vertices);
   if no_vertices < 3
      error('getAreaFrom3DPolygon:General','Too few vertices.');
   end
   
   v = nan(3,no_vertices);
   
   % move them such that one vertex is in the origin
   if isstruct(vertices)
      for i=1:no_vertices
         v(1,i) = vertices(i).x-vertices(1).x;
         v(2,i) = vertices(i).y-vertices(1).y;
         v(3,i) = vertices(i).z-vertices(1).z;
      end
   else
      v = vertices-repmat(vertices(:,1),1,no_vertices);
   end
   
   % calculate the normals between neighboring vertices
   normals = [];
   
   for i=2:no_vertices-1
      tmp = cross(v(:,i),v(:,i+1));
      if norm(tmp) == 0 % corresponds to three points on a line...
         continue;
      end
      normals = [normals, tmp/norm(tmp)];
   end
   
   % get the maximum 'tiltedness' between the triangles defined by the origin, vertex(i) and vertex(i+1)
   max_delta_theta = 0;
   for i=1:size(normals,2)
      for j=i+1:size(normals,2)
         delta_theta = abs(atan2(norm(cross(normals(:,i),normals(:,j))),dot(normals(:,i),normals(:,j)))); % this is more accurate than just acos(dot(.,.))
         delta_theta = min(delta_theta,abs(delta_theta-pi));
         if delta_theta > max_delta_theta
            max_delta_theta = delta_theta;
         end
      end
   end
   
   if max_delta_theta > 1*(2*pi/360) % if they are tilted more than 1 degree
      error('Tiltedness exceeds threshold');
   end
   
   % if we're here, we made sure that the vertices actually define a planar area, we now do a coordinate transformation to (x',y',z') such that z' is close to zero
   if norm(sum(normals,2)) == 0
      normals(:,1) = -normals(:,1);
   end
   avg_normal = sum(normals,2)/norm(sum(normals,2)); % this will be the z' coordinate
   x_prime_norm = v(:,2)/norm(v(:,2));
   z_prime_norm = avg_normal;
   y_prime_norm = cross(z_prime_norm,x_prime_norm); % the result should be a right-handed orthogonal coordinate system which is why y=cross(z,x)
   
   T_prime = [x_prime_norm,y_prime_norm,z_prime_norm];
   v_prime = T_prime\v;
   v_prime_2D = v_prime(1:2,:);
   A = polyarea(v_prime_2D(1,:)',v_prime_2D(2,:)');
   
   if isnan(A)
      error('isnan A');
   end
   
end


