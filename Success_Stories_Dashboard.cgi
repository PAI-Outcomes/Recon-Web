require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;
use Date::Calc qw(Delta_Days);

$| = 1;

my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

my @today = (localtime)[5,4,3];
$today[0] += 1900;
$today[1]++;

&readsetCookies;
&readPharmacies();
&readCSRs();
&readThirdPartyPayers;

$inNCPDP = $in{'NCPDPNumber'};
$csr     = $in{'csr'};
$sortby  = $in{'sortby'};
$action  = $in{'action'};

#$USER = 70;

$inNCPDP = substr($inNCPDP,0,7);
my $csr_name = $CSR_Reverse_ID_Lookup{$USER};

$fNCPDP = sprintf("%07d", $inNCPDP);
$ph_id   = $Reverse_Pharmacy_NCPDPs{$fNCPDP};

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&add_intervention() if ( $action =~ /Add/i );

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
   my $complete_checked = '';
   my $archived_checked = '';

   print qq#<script>
              \$(document).ready(function() {
                 \$('input[name=status]').change(function(){
                    \$('form[name=selectForm]').submit();
                 });
              });
            </script>#;

   print qq#<!-- displayWebPage -->\n#;
 
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
 
   ($PROG = $prog) =~ s/_/ /g;

   print qq#<a href="Intervention_Dashboard.cgi">Return to Interventions</a>\n#;

   print qq#<h2>Success Stories</h2>\n#;

   print qq#<form id="selectForm" action="Success_Stories_Dashboard.cgi" method="post">#;
   print qq#<input type="hidden" id="inv_det_id" name="inv_det_id" value="">#;
   print qq#<input type="hidden" id="sortby" name="sortby" value="">#;
   print "<table>\n";

   print qq#<tr><th><label for="NCPDPNumber">Pharmacy:</label></th>#;
   print qq#<th><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$inNCPDP" style="width:300px;"></th>\n#;
   print qq#<td style="border: none"><datalist id="plist" >#;

   my $DBNAME = "officedb";
   my $TABLE  = "pharmacy";

   my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
                FROM officedb.pharmacy 
               WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
                  && NCPDP NOT IN (1111111,2222222,3333333,5555555)
           UNION ALL
              SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
                FROM officedb.pharmacy_coo
               WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
                  && NCPDP NOT IN (1111111,2222222,3333333,5555555)
            ORDER BY Pharmacy_Name";

   my $sthx  = $dbx->prepare("$sql");
   $sthx->execute;

   while ( my ($ph_id, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
     print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
   }

   $sthx->finish;
   print qq#</datalist>&nbsp;<INPUT class="button-form-xsmall" TYPE="submit" NAME="Select" VALUE="Search"></td></tr>#;

   print qq#<tr style="border: none">
 	     <th style="border: none">
 	       <label for="csr">Account Manager:</label>
	     </th>
	     <td style="border: none">
               <select name="csr" id="csr">
                 <option value='' selected>Select...</option>#;

   foreach my $id (sort { $CSR_Names{$a} cmp $CSR_Names{$b} } keys %CSR_Names) {
     if ( $csr =~ /$CSR_Names{$id}/i ) {
       $selected = 'SELECTED';
     }
     else {
       $selected = '';
     }
     print qq#<option value='$CSR_Names{$id}' $selected>$CSR_Names{$id}</option>#;
   }

   print qq#   </select>
	     </td>
	   </tr>
           <tr>
             <td style="border: none"><INPUT class="button-form-xsmall" TYPE="button" NAME="New" VALUE="New Success Story" onClick="new_intervention()"></td>
             <td style="border: none"><INPUT class="button-form-xsmall" TYPE="button" NAME="download" VALUE="Report" onClick="getReport()"><div id='file_link' style='margin-left: 5px; display: inline-block;'></div></td>
           </tr>
         </table>#;

   print qq#</form><br>#;

   print qq#<script type="text/javascript" charset="utf-8" src="https://code.jquery.com/jquery-3.5.1.js"></script> \n#;
   #print '<link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css" />';
   print '<script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>';
   print '<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>';

   print qq#<script type="text/javascript" charset="utf-8">
           function showHideRow(row) {
               \$("\#" + row).toggle();
           }

           function sort_records(col) {
              \$("\#sortby").val(col);
              \$("\#selectForm").submit();
           }

           function getReport() {
             document.getElementById("file_link").innerHTML = "Working...";
             var xhttp = new XMLHttpRequest();
             setTimeout(function() {

             xhttp.onreadystatechange=function() {
               if (this.readyState == 4 && this.status == 200) {
                 var r = this.response;
                 if (r.match(/ERROR/g)) {
                   alert("Report Failed: Please Contact IT\\n");
                 }
                 else { 
                   document.getElementById("file_link").innerHTML = "<a href='" + r + "' style='background: \#133562; padding: 4px; text-align: center; border-radius: 5px; color: white;' download>Download</a>";
//                   document.getElementById("file_link").innerHTML = r;
                 }
               }
             };

             var url = "../includes/RunReport.pl?ph_id=$ph_id&csr='$csr'";
             xhttp.open("POST", url, false);
             xhttp.send();
             }, 10);
           }
   
           function checkinfo(){
             var thisform = 'form1';
             var message = '';
             var errors  = 0;
	     var doc = document.forms[thisform];

	     if(doc["add_ncpdp"].value == '') {
               doc["add_ncpdp"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_payer"].value == '') {
               doc["add_payer"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_amount"].value == '') {
               doc["add_amount"].style.borderColor = "red";
               errors++;
	     }

	     if(errors){
	       return false; 
	     }	   
	     else {
	       return true;
	     }
           }

           \$(function() {
             var thisform = 'form1';
	     var doc = document.forms[thisform];
             \$( "\#dialog-form1" ).dialog({
	  	autoOpen: false,
		height: 250,
		width: 650,
		modal: true,
		buttons: {
			"Save": function() {
                                      var tf  = checkinfo();
					if(tf) {
					  \$('\#form1').submit();
					}
				},
			Cancel: function() {
                                        doc["add_ncpdp"].value = '';
                                        doc["add_ncpdp"].style.borderColor = "black";
                                        doc["add_payer"].value = '';
                                        doc["add_payer"].style.borderColor = "black";
                                        doc["add_amount"].value = '';
                                        doc["add_amount"].style.borderColor = "black";
					\$( this ).dialog( "close" );
				}
			},
			close: function() {
				
			}
		});
           });

           function new_intervention() {
             var sel_ncpdp = \$("\#NCPDP").val();
             \$("\#add_ncpdp").val(sel_ncpdp);
             \$("\#dialog-form1").dialog("open");
           }
         </script> \n#;

   print qq#<style>
        \#table_detail {
            background-color: \#FFFFFF;
        }

        \#table_master .hidden_row {
            display: none;
        }

        \#table_master tr:hover {
            cursor: pointer;
        }

        \#table_detail th {
            font-size: 110%;
        }
    </style>\n#;

   print qq#<table id="table_master">\n#;
   print "<thead>\n";
   print qq#<tr>
              <th>Year</th>
              <th style="text-align: center">Story Count</th>
              <th style="text-align: right">Total Amount</th>
            </tr>\n#;
   print "</thead>\n";
   print "<tbody>\n";

   my $numrowsc = 0;
   my $sql = "";
   my $and = "";

   $and .= "AND a.Pharmacy_ID = '$ph_id'" if ( $ph_id );
   $and .= "AND CSR_Name = '$csr'" if ( $csr );

   if ( $sortby && $stortby !~ /Closed_Date/i ) {
     $order = $sortby;
   }
   else {
     $order = 'Closed_Date DESC';
   }

   $sql = "SELECT Intervention_ID, a.Pharmacy_ID, 
               CASE
                 WHEN a.Type = 'ThirdPartyPayer' THEN concat('TPP:', Third_Party_Payers.Third_Party_Payer_Name)
                 WHEN a.Type = 'Vendor' THEN concat('VEN:', Vendor.Vendor_Name)
               END AS Type, CSR_Name, DATE(Closed_Date), YEAR(DATE(Closed_Date)), Recon_Success_Story
             FROM officedb.interventions a
             JOIN officedb.Pharmacy b ON (a.Pharmacy_ID = b.Pharmacy_ID)
        LEFT JOIN officedb.Third_Party_Payers ON (Type_ID = Third_Party_Payer_ID)
        LEFT JOIN officedb.Vendor ON (Type_ID = Vendor_ID)
            WHERE Recon_Success_Story IS NOT NULL
              $and
         ORDER BY YEAR(DATE(Closed_Date)) DESC, $order";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;

##   print "SQL: $sqlout";

   $sthrp = $dbx->prepare($sql);
   $sthrp->execute();
   my $numofrows = $sthrp->rows;
   my $inv_id_sav = 0;
   my $detail_count = 0;

   while ( my ( $inv_id, $Pharmacy_ID, $type, $csr, $sdate, $syear, $amount ) = $sthrp->fetchrow_array()) {
     if ( $syear != $syear_sav ) {
       #### Finish Master Row
       if ( $syear_sav ) {
         $year_amount = &commify(sprintf("%0.2f", $year_amount));
         print qq#<td align="center">$detail_count</td>\n#;
#         print qq#<td align="right"><a href="javascript:showHideRow('hidden_$inv_id_sav')">$detail_count</a></td>\n#;
         print qq#<td align="right">\$$year_amount</td>\n#;

         print qq#</tr>\n#;

         #### Add Detail Rows
         print qq#<tr id="hidden_$syear_sav" class="hidden_row">
                    <td colspan=8>
                      <table id="table_detail">
                        <tr>
                          <th><a href="javascript:sort_records('Closed_Date')">Date</a></th>
                          <th><a href="javascript:sort_records('Pharmacy_ID')">Pharmacy</a></th>
                          <th>Type</th>
                          <th><a href="javascript:sort_records('CSR_Name')">CSR</a></th>
                          <th><a href="javascript:sort_records('Type')">Payer</a></th>
                          <th>Amount</th>
                        </tr>\n
                        $hidden_rows
                      </table>
                    </td>
                  </tr>\n#;

#                        <tr style="border: none;">
#                          <td colspan=3><input type="text" id="comm_$inv_id_sav" name="comm_$inv_id_sav" size="110">&nbsp <input type='button' class="button-form-xsmall" id="comm_btn_$inv_id_sav" name='comment_btn' value='Add Comment' onClick='add_comm("$inv_id_sav", this.value);'></td>
#                        </tr>\n
       }

       $color = '#5FC8ED';

       print qq#<tr id="Row_$syear" style="background-color: $color; color: \#000000;" onClick="javascript:showHideRow('hidden_$syear')">\n#;
       print qq#<td nowrap>$syear</td>\n#;

       $hidden_rows  = '';
       $detail_count = 0;
       $year_amount  = 0;
     }

     #### Build Detail Rows
     my ($iYear, $iMonth, $iDay) = split("-", $sdate, 3);
     $sdate = "$iMonth/$iDay/$iYear";
     my $famount = &commify(sprintf("%0.2f", $amount));
     my $ptype = 'ReconRx';

     if ( $Pharmacy_Software_Vendors{$Pharmacy_ID} =~ /Rx30|ComputerRx/i ) { 
       $ptype = 'TDS';
     }

     if ( $Pharmacy_Current_PSAOs{$Pharmacy_ID} =~ /Arete/i ) { 
       if ( $ptype =~ /TDS/i ) {
         $ptype .= '/Arete';
       }
       else {
         $ptype = 'Arete';
       }
     }

     $hidden_rows .= qq#<tr style="border: none;">
                          <td nowrap>$sdate</td>
                          <td nowrap>$Pharmacy_Names{$Pharmacy_ID}</td>
                          <td nowrap>$ptype</td>
                          <td nowrap>$csr</td>
                          <td nowrap>$type</td>
                          <td align="right" nowrap>\$$famount</td>\n#;
     $hidden_rows .= qq#</tr>\n#;
     ++$detail_count;

     $syear_sav  = $syear;
     $year_amount += $amount;
   }

   #### Finish Last Record
   $year_amount = &commify(sprintf("%0.2f", $year_amount));
   print qq#<td align="center"><a href="javascript:showHideRow('hidden_$syear_sav')">$detail_count</a></td>\n#;
   print qq#<td align="right">\$$year_amount</td>\n#;

   print qq#</tr>\n#;

   #### Add Detail Rows
   print qq#<tr id="hidden_$syear_sav" class="hidden_row"><td colspan=8><table id="table_detail" style="width: 100%">$hidden_rows#;

   print qq#<tr style="border: none;">
              <td colspan=3><input type="text" id="comm_$inv_id_sav" name="comm_$inv_id_sav" size="110">&nbsp <input type='button' class="button-form-xsmall" id="comm_btn_$inv_id_sav" name='comment_btn' value='Add Comment' onClick='add_comm("$inv_id_sav", this.value);'></td>
            </tr>\n#;
   print qq#</table></td></tr>\n#;

   $sthrp->finish;
 
   print qq#</tbody>\n#;
   print qq#</table>\n#;

   #### Hidden Input Form1
   print qq#<div id="dialog-form1" title="Add Success Story" style="display: none;">
       <form id="form1" action="Success_Stories_Dashboard.cgi" method="post">
         <input type="hidden" id="action" name="action" value="Add">
         <table class="tableNoBorder">
	   <tr style="border: none">
 	     <td style="border: none">
 	       <label for="add_ncpdp">Pharmacy</label>
	     </td>
	     <td style="border: none">
               <select name="add_ncpdp" id="add_ncpdp">
                 <option value='' selected>Select...</option>#;

   foreach my $Pharmacy_ID (sort { $Pharmacy_NCPDPs{$a} cmp $Pharmacy_NCPDPs{$b} } keys %Pharmacy_NCPDPs) {
     next if ( $Pharmacy_Status_ReconRxs{$Pharmacy_ID} !~ /Active|Pending|Transition/i );
     print qq#<option value='$Pharmacy_NCPDPs{$Pharmacy_ID}'>$Pharmacy_NCPDPs{$Pharmacy_ID} - $Pharmacy_Names{$Pharmacy_ID}</option>#;
   }

   print qq#   </select>
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	       <label for="add_payer">Payer</label>
	     </td>
	     <td style="border: none">
               <select name="add_payer" id="add_payer">
                 <option value='' selected>Select...</option>#;

   foreach $TPP_ID (sort { $ThirdPartyPayer_Names{$a} cmp $ThirdPartyPayer_Names{$b} } keys %ThirdPartyPayer_Names) {
     next if ( $TPP_PriSecs{$TPP_ID} !~ /Pri/i );
     print qq#<option value='$TPP_ID'>$ThirdPartyPayer_Names{$TPP_ID}</option>#;
   }

   print <<BM;   
              </select>
	    </td>
	  </tr>
          <tr>
	    <td style="border: none">
	      <label for="add_amount">Amount</label><br/>
	    </td>
	    <td style="border: none">
              <input type="text" name="add_amount" id="add_amount" class="text ui-corner-all" size="10">
	    </td>	
	  </tr>
	</table>
      </form>
    </div>
BM
}

#______________________________________________________________________________

sub add_intervention {
  my $ncpdp    = $in{'add_ncpdp'};
  my $type     = 'ThirdPartyPayer';
  my $category = 'ReconRx - Pending Success Story';
  my $payer    = $in{'add_payer'};
  my $amount   = $in{'add_amount'};
  my $ph_id    = $Reverse_Pharmacy_NCPDPs{$ncpdp};
  my $date      = &build_date();
  my $date_TS   = &build_date_TS($date);

  $amount =~ s/^\$|,//g;

  $sql = "INSERT 
            INTO officedb.interventions (Pharmacy_ID, Type, Type_ID, Category, Program, CSR_ID, CSR_Name, Status, Opened_Date_TS, Opened_Date, Closed_Date_TS, Closed_Date, Recon_Success_Story)
          VALUES ($ph_id, '$type', $payer, '$category', 'ReconRx', $USER, '$csr_name', 'Closed', '$date_TS', '$date', '$date_TS', '$date', $amount)"; 

#  print "SQL:\n$sql<br>\n";

  my $sthx = $dbx->prepare($sql);
  $sthx->execute() or die $DBI::errstr;
  $row_cnt = $sthx->rows;

  if ( $row_cnt != 1 ) {
    print "Insert Failed<br>";
  }
  else {
    print "Success Story Created<br>";
  }

  $sthx->finish;
}

