


function mFiles = getAllMFiles(folderName,ignoreDirs,ignoreFiles,inExt)
   % GETALLMFILES Recursively gets all m-files in a directory, ignoring specified files and directories.   
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
   
   
   if nargin<4
      inExt = '.m';
   end
   
   
   mFiles = {};
   
   d = dir(folderName);
   d_name = {d.name};
   
   inds_ignoreDirs = [find(strcmp('.',d_name)),find(strcmp('..',d_name))];
   for i=1:length(ignoreDirs)
      ind = find(strcmp(ignoreDirs{i},d_name));
      if ~isempty(ind)
         inds_ignoreDirs(end+1) = ind;
      end
   end
   
   inds_ignoreFiles = [];
   for i=1:length(ignoreFiles)
      ind = find(strcmp(ignoreFiles{i},d_name));
      if ~isempty(ind)
         inds_ignoreFiles(end+1) = ind;
      end
   end
   
   d([inds_ignoreFiles,inds_ignoreDirs]) = [];
   d_name = {d.name};
   
   inds_restDirs = find([d.isdir]);
   inds_restFiles = setdiff(1:length(d_name),inds_restDirs);
   
   for ind = inds_restFiles
      [~,~,ext] = fileparts(d_name{ind});
      if strcmp(inExt,ext)
         mFiles{end+1} = [folderName,filesep,d_name{ind}];
      end
   end
   
   
   for ind = inds_restDirs
      tmp = getAllMFiles([folderName,filesep,d_name{ind}],ignoreDirs,ignoreFiles,inExt);
      mFiles = cat(2,mFiles,tmp);
   end

   
end


