function check_xls_file_header(header_cell,correct_header_cell,fileXLS,~)
   %CHECK_XLS_FILE_HEADER Checks whether the header of the .xls file associated with the specific data fulfills convention.
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
   
   
   
   
   if ~(length(header_cell) == length(correct_header_cell)) || ~isempty(setdiff(header_cell,correct_header_cell))
      error('XLSFile:Header','File ''%s'' has inappropriate header.\nCurrent header:\t\t %s\nREQUIRED header:\t %s\n',...
         fileXLS,sprintf('''%s'' ' ,header_cell{:}),sprintf('''%s'' ' ,correct_header_cell{:}));
   end
end
