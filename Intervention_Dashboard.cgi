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

$inNCPDP = $in{'NCPDPNumber'};
$status  = $in{'status'};
$sortby  = $in{'sortby'};
$action  = $in{'action'};
$csr     = $in{'csr'};

$inNCPDP = substr($inNCPDP,0,7);
my $csr_name = $CSR_Reverse_ID_Lookup{$USER};

$fNCPDP = sprintf("%07d", $inNCPDP);
$ph_id   = $Reverse_Pharmacy_NCPDPs{$fNCPDP};
$csr = $USER if (!$csr);

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

#&readAffiliates;
&readVendors;
&readThirdPartyPayers;

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

   if ( $status =~ /All/i ) {
     $all_checked = 'checked';
   }
   elsif ( $status =~ /Closed/i ) {
     $closed_checked = 'checked';
   } else {
     $active_checked = 'checked';
   }

   print qq#<h2>Interventions</h2>\n#;

   print qq#<form id="selectForm" action="Intervention_Dashboard.cgi" method="post">#;
   print qq#<input type="hidden" id="inv_det_id" name="inv_det_id" value="">#;
   print qq#<input type="hidden" id="sortby" name="sortby" value="">#;
   print "<table>\n";

   print qq#<tr><th><label for="NCPDPNumber">Pharmacy:</label></th>#;
   print qq#<th><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$inNCPDP" style="width:300px;">\n#;
   print qq#<datalist id="plist" >#;

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

   print qq#</datalist>&nbsp;<INPUT class="button-form-xsmall" TYPE="submit" NAME="Select" VALUE="Search"></th></tr>#;

   ### Supervisor RAM Selector
   if ( $USER =~ /^74$|^69$/ ) {
     print qq#<tr>
   	       <th>
 	         <label for="csr">Account Manager:</label>
	       </th>
	       <th>
                 <select name="csr" id="csr">
                   <option value='' selected>Select...</option>#;

     foreach my $id (sort { $CSR_Names{$a} cmp $CSR_Names{$b} } keys %CSR_Names) {
        next if(!$CSR_Recon_Ram{"$id"});
  
       if ( $csr =~ /$CSR_SuperUsers{$id}/i ) {
         $selected = 'SELECTED';
       }
       else {
         $selected = '';
       }
       print qq#<option value='$CSR_SuperUsers{$id}' $selected>$CSR_Names{$id}</option>#;
     }

     print qq#   </select>
  	       </th>
	     </tr>#;
   }

   print qq#</table>#;

   print qq#<INPUT TYPE="radio" NAME="status" VALUE="Active" $active_checked> Active
            <INPUT TYPE="radio" NAME="status" VALUE="Closed" $closed_checked> Closed
            <INPUT TYPE="radio" NAME="status" VALUE="All" $all_checked> All
            </form><br>#;

   print qq#<div style="position: relative; display: inline-block; float: left; margin-bottom: 15px; width: 40%">
              <strong>New Intervention:</strong>
              <select name="inv_select" onchange="new_intervention(this.value)">
                <option value='' selected>Select...</option>
                <option value='ThirdPartyPayer'>Third Party Payer</option>
                <option value='Vendor'>Vendor</option>
              </select>
              <form action="Success_Stories_Dashboard.cgi" method="post" style="position: relative; display: inline-block; float: right">
                <INPUT class="button-form-xsmall" TYPE="submit" VALUE="Success Stories">\n
              </form>
            </div><br><br>#;

   if ( $ph_id ) {
     $and = "AND b.NCPDP = '$inNCPDP'";
   }
   else {
     $and = "AND a.CSR_ID = $csr";
   }

   $sqla = "SELECT
                CASE 
                  WHEN (Category = 'ReconRx - 835 Remits Initial Setup' OR Category = 'ReconRx - Payment Confirmation Requested' OR Category = 'ReconRx - Pharmacy Claim Research' OR Category = 'ReconRx - Tuesday Pending Payment Reminder') THEN 'Auto'
                  WHEN DATEDIFF(DATE(CURRENT_TIMESTAMP), DATE(a.Last_Touched)) > 28 THEN 'Action'
                  ELSE 'Open'
                END AS int_type, count(*)
              FROM officedb.interventions a
              JOIN officedb.pharmacy b ON (a.Pharmacy_ID = b.Pharmacy_ID)
             WHERE a.status = 'Active'
               AND b.Status_ReconRx IN ('Active','Transition')
               AND a.Opened_Date >= '2017-01-01 00:00:00'
               $and
          GROUP BY int_type";

#   print "$sqla<br>";

   my $stha = $dbx->prepare("$sqla");
   $stha->execute;

   %active = ('Open' => '0', 'Action' => '0', 'Auto' => '0');

   while ( my ($type, $cnt) = $stha->fetchrow_array() ) {
     $active{$type} = $cnt;
   }

   $stha->finish;

   print qq#<div style="position: relative; display: block; float: left; margin-bottom: 15px; width: 50%">
              <table>
                <tr style="color: \#000000;">
                  <td nowrap style="border: none;">Table Key:</td>
                  <td style="background-color: \#5FC8ED; width: 100px; border: none; text-align: center;">Open ($active{'Open'})</td>
                  <td style="background-color: \#ff1a1a; width: 100px; border: none; text-align: center;">Attention ($active{'Action'})</td>
                  <td style="background-color: yellow; width: 100px; border: none; text-align: center;">Updated</td>
                  <td style="background-color: \#133562; color: \#FFFFFF; width: 100px; border: none; text-align: center;">Closed</td>
                  <td style="background-color: \#808080; width: 100px; border: none; text-align: center;">Auto ($active{'Auto'})</td>
                </tr>
              </table>
            </div>#;

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

           function edit_comment(inv_id, det_id, comment) {
              var elem = 'comm_' + inv_id;
              \$("\#" + elem).val(comment);
              \$("\#inv_det_id").val(det_id);
              \$("\#comm_btn_" + inv_id).val('Update Comment');
           }

           function cancel_comm(inv_id) {
              var elem = 'comm_' + inv_id;
              \$("\#" + elem).val('');
              \$("\#comm_btn_" + inv_id).val('Add Comment');
           }

           function close_intervention(inv_id) {
              var elem = 'comm_' + inv_id;
              var hd   = 'hidden_' + inv_id;
              if ( document.getElementById(hd).style.display == '' || document.getElementById(hd).style.display == 'none') {
                showHideRow(hd);
              }
              \$("\#" + elem).val('');
              \$("\#comm_btn_" + inv_id).val('Save and Close');
           }

           function add_comm(inv_id, btn) {
              var elem = 'comm_' + inv_id;
              var row  = 'Row_' + inv_id;
              var hd   = 'hidden_' + inv_id;

              if ( document.getElementById(elem).value == '' ) {
                alert('Please enter Note');
              }
              else {
                var comm = document.getElementById(elem).value;
                var inv_det_id = document.getElementById('inv_det_id').value;
                \$.ajax("../ajax/save_comment.pl", {
                    data: {
                        id: inv_id,
                        det_id: inv_det_id,
                        comment: comm,
                        action: btn,
                        csr: $USER,
                        csr_name: '$csr_name'
                    }
                })
                .then(
                  function success(retval) {
                    if ( retval ) {
                      document.getElementById(row).style.backgroundColor = "yellow";
                      showHideRow(hd);
                      \$("\#" + elem).val('');
                      \$("\#comm_btn_" + inv_id).val('Add Comment');
                    }
                    else {
                      alert('Comment could not be saved.');
                    }
                  },

                  function fail(data, status) {
                      alert('Request failed.  Returned status of ' + status);
                  }
                );
              }
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
	     if(doc["add_category"].value == '') {
               doc["add_category"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_payer"].value == '') {
               doc["add_payer"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_note"].value == '') {
               doc["add_note"].style.borderColor = "red";
               errors++;
	     }

	     if(errors){
	       return false; 
	     }	   
	     else {
	       return true;
	     }
           }

           function checkinfo2(){
             var thisform = 'form2';
             var message = '';
             var errors  = 0;
	     var doc = document.forms[thisform];

	     if(doc["add_ncpdp"].value == '') {
               doc["add_ncpdp"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_category"].value == '') {
               doc["add_category"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_payer"].value == '') {
               doc["add_payer"].style.borderColor = "red";
               errors++;
	     }
	     if(doc["add_note"].value == '') {
               doc["add_note"].style.borderColor = "red";
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
		height: 300,
		width: 700,
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
                                        doc["add_category"].value = '';
                                        doc["add_category"].style.borderColor = "black";
                                        doc["add_payer"].value = '';
                                        doc["add_payer"].style.borderColor = "black";
                                        doc["add_note"].value = '';
                                        doc["add_note"].style.borderColor = "black";
					\$( this ).dialog( "close" );
				}
			},
			close: function() {
				
			}
		});
           });

           \$(function() {
             var thisform = 'form2';
	     var doc = document.forms[thisform];
             \$( "\#dialog-form2" ).dialog({
	  	autoOpen: false,
		height: 300,
		width: 700,
		modal: true,
		buttons: {
			"Save": function() {
                                      var tf  = checkinfo2();
					if(tf) {
					  \$('\#form2').submit();
					}
				},
			Cancel: function() {
                                        doc["add_ncpdp"].value = '';
                                        doc["add_ncpdp"].style.borderColor = "black";
                                        doc["add_category"].value = '';
                                        doc["add_category"].style.borderColor = "black";
                                        doc["add_payer"].value = '';
                                        doc["add_payer"].style.borderColor = "black";
                                        doc["add_note"].value = '';
                                        doc["add_note"].style.borderColor = "black";
					\$( this ).dialog( "close" );
				}
			},
			close: function() {
				
			}
		});
           });

           function new_intervention(type) {
             var sel_ncpdp = \$("\#NCPDP").val();
             if ( type == 'ThirdPartyPayer' ) {
               \$("\#add_ncpdp1").val(sel_ncpdp);
               \$("\#dialog-form1").dialog("open");
             }
             if ( type == 'Vendor' ) {
               \$("\#add_ncpdp2").val(sel_ncpdp);
               \$("\#dialog-form2").dialog("open");
             }
           }
         </script> \n#;

   print qq#<style>
        \#table_detail {
            background-color: \#FFFFFF;
        }

        \#table_master .hidden_row {
            display: none;
        }

        \#table_master th:hover {
            font-weight: bold;
        }

        \#table_master td {
            border-top: 1px solid \#000000;
        }

        \#table_master td.link:hover {
            cursor: pointer;
        }
    </style>\n#;

   print qq#<table id="table_master">\n#;
   print "<thead>\n";
   print qq#<tr>
              <th><a href="javascript:sort_records('Pharmacy_Name')">Pharmacy</a></th>
              <th><a href="javascript:sort_records('NCPDP')">NCPDP</a></th>
              <th><a href="javascript:sort_records('Category')">Category</a></th>
              <th><a href="javascript:sort_records('Type')">Type</a></th>
              <th><a href="javascript:sort_records('Opened_Date')">Opened (Days Ago)</a></th>
              <th><a href="javascript:sort_records('Last_Touched')">Updated (Days Ago)</a></th>
              <th>Upds</th>
              <th></th>
            </tr>\n#;
   print "</thead>\n";
   print "<tbody>\n";

   if ($status =~ /All/i) {
     $status = "'Active','Closed'";
   }
   elsif ($status =~ /Closed/i) {
     $status = "'Closed'";
   }
   else {
     $status = "'Active'";
   }

   my $numrowsc = 0;
   my $sql = "";

   if ( $sortby ) {
     $order = $sortby;
   }
   else {
     $order = 'a.status, a.Opened_Date';
   }

   $sql = "SELECT c.Row_Intervention_Row_ID, a.Intervention_ID, a.Pharmacy_ID,
               CASE
                 WHEN a.Type = 'ThirdPartyPayer' THEN concat('TPP:', d.Third_Party_Payer_Name)
                 WHEN a.Type = 'Vendor' THEN concat('VEN:', e.Vendor_Name)
               END AS Type, a.Category, a.Opened_Date, a.Last_Touched, a.CSR_Name, a.Status, a.Comments, c.Row_CSR_Name, c.Row_Date, c.Row_Comments
             FROM officedb.interventions a
             JOIN officedb.pharmacy b ON (a.Pharmacy_ID = b.Pharmacy_ID)
             LEFT JOIN officedb.int_rows c ON (a.Intervention_ID = c.Row_Intervention_ID)
             LEFT JOIN officedb.Third_Party_Payers d ON (a.Type_ID = d.Third_Party_Payer_ID)
             LEFT JOIN officedb.Vendor e ON (a.Type_ID = e.Vendor_ID)
            WHERE a.status IN ($status)
              AND b.Status_ReconRx IN ('Active','Transition')
              AND a.Opened_Date >= '2017-01-01 00:00:00'
              $and
         ORDER BY $order";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;

#   print "SQL: $sqlout";

   $sthrp = $dbx->prepare($sql);
   $sthrp->execute();
   my $numofrows = $sthrp->rows;
   my $inv_id_sav = 0;
   my $detail_count = 0;
   my $isauto = 0;

   while ( my ( $det_id, $inv_id, $Pharmacy_ID, $itype, $cat, $odate, $ltdate, $icsr, $status, $icomm, $ucsr, $det_date, $comm ) = $sthrp->fetchrow_array()) {
     if ( $inv_id != $inv_id_sav ) {
       my ($Opened_Date_Out) = &FixDBDate($odate);
       my ($Last_Touched_Out) = &FixDBDate($ltdate);
       $jcomm = $comm;
       $jcomm =~ s/\'/\\'/g;

       #### Finish Master Row
       if ( $inv_id_sav ) {
          print qq#<td>$detail_count</td>\n#;

         if ( $status_sav =~ /Closed/i || ($isauto && $USER !~ /^69$|^74$|^70$|^2387$/)) {
           print qq#<td>$status_sav</td>\n#;
         }
         else {
           print qq#<td><form action="Intervention_Action.cgi" method="post">
                          <INPUT class="button-form-xsmall" TYPE="button" VALUE="Close" onClick='close_intervention($inv_id_sav);'>
                        </form>
                    </td>\n#;
         }

         print qq#</tr>\n#;

         #### Add Detail Rows
         if ( $detail_count || $status_sav =~ /Active/i ) {
           print qq#<tr id="hidden_$inv_id_sav" class="hidden_row"><td colspan=8><table id="table_detail" style="width: 100%">$hidden_rows#;

           if ( $status_sav =~ /Active/i ) {
             print qq#<tr style="border: none;">
                        <td colspan=3><input type="text" id="comm_$inv_id_sav" name="comm_$inv_id_sav" size="110">&nbsp <input type='button' class="button-form-xsmall" id="comm_btn_$inv_id_sav" name='comment_btn' value='Add Comment' onClick='add_comm("$inv_id_sav", this.value);'>&nbsp <input type='button' class="button-form-xsmall" name='cancel_btn' value='Cancel' onClick='cancel_comm("$inv_id_sav");'></td>
                      </tr>\n#;
           }

           print qq#</table></td></tr>\n#;
         }

       }

       my ($p1, $p2) = split(" ", $odate, 2);
       my ($iYear, $iMonth, $iDay) = split("-", $p1, 3);
       my @IOD = ($iYear, $iMonth, $iDay);

       $ODaysAgo = Delta_Days(@IOD, @today);

       my ($p1, $p2) = split(" ", $ltdate);
       my ($iYear, $iMonth, $iDay) = split("-", $p1, 3);
       my @ILT = ($iYear, $iMonth, $iDay);

       $UDaysAgo = Delta_Days(@ILT, @today);

       #### Change Row Color depending on Status
       if ( $status =~ /Active/i ) {
         $color = '#000000';

         if ( $UDaysAgo > 28 ) {
           $bg_color = '#ff1a1a';
         }
         else {
           $bg_color = '#5FC8ED';
         }
       }
       else {
         $color = '#FFFFFF';
#         $bg_color = '#009900';
         $bg_color = '#133562';
       }

       if ( $cat =~ /ReconRx - 835 Remits Initial Setup|ReconRx - Payment Confirmation Requested|ReconRx - Pharmacy Claim Research/i || $cat =~ /ReconRx - Tuesday Pending Payment Reminder/i) {
         $bg_color = '#808080' if ( $status =~ /Active/i );
         $isauto = 1;
       }
       else {
         $isauto = 0;
       }

       print qq#<tr id="Row_$inv_id" style="background-color: $bg_color; color: $color;">\n#;
       print qq#<td nowrap class="link" onClick="javascript:showHideRow('hidden_$inv_id')">$Pharmacy_Names{$Pharmacy_ID}</td>\n#;
       print qq#<td>$Pharmacy_NCPDPs{$Pharmacy_ID}</td>\n#;
       print qq#<td nowrap>$cat</td>\n#;
       print qq#<td nowrap>$itype</td>\n#;
       print qq#<td nowrap>$Opened_Date_Out ($ODaysAgo)</td>\n#;
       print qq#<td nowrap>$Last_Touched_Out ($UDaysAgo)</td>\n#;

       $hidden_rows = qq#<tr style="border: none; font-weight: bold;"><td style="width: 130px" nowrap>$icsr</td><td nowrap colspan=3>$icomm</td>#;
       $detail_count = 0;
     }

     #### Build Detail Rows
     if ( $det_id ) {
       my ($Follow_Up_Date) = &FixDBDate($det_date);

       $hidden_rows .= qq#<tr style="border: none;">
                            <td nowrap style="width: 130px">$ucsr</td>
                            <td nowrap style="width: 150px">$Follow_Up_Date</td>
                            <td>$comm</td><td></td>#;

       if ( $isauto || $status =~ /Closed/i ) {
         $hidden_rows .= qq#<td nowrap>&nbsp</td>#;
       }
       else {
         $hidden_rows .= qq#<td nowrap><input type='button' class="button-form-xsmall" name='edit_comment' value='Edit' onClick="edit_comment($inv_id, $det_id, '$comm');"></td>#;
       }

       $hidden_rows .= qq#</tr>\n#;
       ++$detail_count;
     }

     $inv_id_sav = $inv_id;
     $status_sav = $status;
   }

   #### Finish Last Record
   print qq#<td>$detail_count</td>\n#;

   if ( $status_sav =~ /Closed/i || ($isauto && $USER !~ /^69$|^74$|^70$|^2387$/)) {
     print qq#<td>$status_sav</td>\n#;
   }
   else {
     print qq#<td><form action="Intervention_Action.cgi" method="post">
                     <INPUT class="button-form-xsmall" TYPE="button" VALUE="Close" onClick='close_intervention($inv_id_sav);'>
                  </form>
                </td>\n#;
   }

   print qq#</tr>\n#;

   #### Finishing Detail Rows
   if ( $detail_count || $status_sav =~ /Active/i ) {
     print qq#<tr id="hidden_$inv_id_sav" class="hidden_row"><td colspan=7><table id="table_detail" style="width: 100%">$hidden_rows#;

     if ( $status_sav =~ /Active/i ) {
       print qq#<tr style="border: none;">
                  <td colspan=3><input type="text" id="comm_$inv_id_sav" name="comm_$inv_id_sav" size="110">&nbsp <input type='button' class="button-form-xsmall" id="comm_btn_$inv_id_sav" name='comment_btn' value='Add Comment' onClick='add_comm("$inv_id_sav", this.value);'>&nbsp <input type='button' class="button-form-xsmall" name='cancel_btn' value='Cancel' onClick='cancel_comm("$inv_id_sav");'></td>
                </tr>\n#;
     }

     print qq#</table></td></tr>\n#;
   }

   $sthrp->finish;
 
   print qq#</tbody>\n#;
   print qq#</table>\n#;

   #### Hidden Input Form1
   print qq#<div id="dialog-form1" title="Add Intervention" style="display: none;">
       <form id="form1" action="Intervention_Dashboard.cgi" method="post">
         <input type="hidden" name="action" value="Add">
         <input type="hidden" name="add_type" value="ThirdPartyPayer">
         <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
         <input type="hidden" name="status" value="$status">
         <input type="hidden" name="sortby" value="$sortby">

         <table class="tableNoBorder">
	   <tr style="border: none">
 	     <td style="border: none">
 	       <label for="add_ncpdp">Pharmacy</label>
	     </td>
	     <td style="border: none">
               <select name="add_ncpdp" id="add_ncpdp1">
                 <option value='' selected>Select...</option>#;

   foreach my $Pharmacy_ID (sort { $Pharmacy_Names{$a} cmp $Pharmacy_Names{$b} } keys %Pharmacy_Names) {
     next if ( $Pharmacy_Status_ReconRxs{$Pharmacy_ID} !~ /Active|Pending|Transition/i );
     print qq#<option value='$Pharmacy_NCPDPs{$Pharmacy_ID}'>$Pharmacy_NCPDPs{$Pharmacy_ID} - $Pharmacy_Names{$Pharmacy_ID}</option>#;
   }

   print qq#   </select>
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	       <label for="add_category">Category</label>
	     </td>
	     <td style="border: none">
               <select name="add_category" id="add_category1">
                 <option value='' selected>Select...</option>#;

   $sql_cat = "SELECT Vals 
                 FROM officedb.opts 
                WHERE OPTS_ID = 1074 #ReconRx Categories
             ORDER BY Vals ASC";

   my $sth_cat = $dbx->prepare("$sql_cat");
   $sth_cat->execute;

   while ( my ($rec) = $sth_cat->fetchrow_array() ) {
     @vals = split(/,/, $rec);

     foreach (@vals) {
       $_ =~ s/^\s*(.*?)\s*$/$1/;
       print "<option value='$_'>$_</option>\n";
     }
   }
   
   $sth_cat->finish();

   print qq#   </select>
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	       <label for="add_payer">Payer</label>
	     </td>
	     <td style="border: none">
               <select name="add_payer" id="add_payer1">
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
	      <label for="add_note">Note</label><br />
	    </td>
	    <td style="border: none">
              <textarea name="add_note" id="add_note1" class="text ui-corner-all" rows="3" cols="55"></textarea>
	    </td>	
	  </tr>
	</table>
      </form>
    </div>
BM

   #### Hidden Input Form2
   print qq#<div id="dialog-form2" title="Add Intervention" style="display: none;">
       <form id="form2" action="Intervention_Dashboard.cgi" method="post">
         <input type="hidden" name="action" value="Add">
         <input type="hidden" name="add_type" value="Vendor">
         <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
         <input type="hidden" name="status" value="$status">
         <input type="hidden" name="sortby" value="$sortby">

         <table class="tableNoBorder">
	   <tr style="border: none">
 	     <td style="border: none">
 	       <label for="add_ncpdp">Pharmacy</label>
	     </td>
	     <td style="border: none">
               <select name="add_ncpdp" id="add_ncpdp2">
                 <option value='' selected>Select...</option>#;

   foreach my $Pharmacy_ID (sort { $Pharmacy_Names{$a} cmp $Pharmacy_Names{$b} } keys %Pharmacy_Names) {
     next if ( $Pharmacy_Status_ReconRxs{$Pharmacy_ID} !~ /Active|Pending|Transition/i );
     print qq#<option value='$Pharmacy_NCPDPs{$Pharmacy_ID}'>$Pharmacy_NCPDPs{$Pharmacy_ID} - $Pharmacy_Names{$Pharmacy_ID}</option>#;
   }

   print qq#   </select>
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	       <label for="add_category">Category</label>
	     </td>
	     <td style="border: none">
               <select name="add_category" id="add_category2">
                 <option value='' selected>Select...</option>#;

   $sql_cat = "SELECT Vals 
                 FROM officedb.opts 
                WHERE OPTS_ID = 1074 #ReconRx Categories
             ORDER BY Vals ASC";

   my $sth_cat = $dbx->prepare("$sql_cat");
   $sth_cat->execute;

   while ( my ($rec) = $sth_cat->fetchrow_array() ) {
     @vals = split(/,/, $rec);

     foreach (@vals) {
       $_ =~ s/^\s*(.*?)\s*$/$1/;
       print "<option value='$_'>$_</option>\n";
     }
   }
   
   $sth_cat->finish();

   print qq#   </select>
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	       <label for="add_payer">Vendor</label>
	     </td>
	     <td style="border: none">
               <select name="add_payer" id="add_payer2">
                 <option value='' selected>Select...</option>#;

   foreach $VND_ID (sort { $Vendor_Names{$a} cmp $Vendor_Names{$b} } keys %Vendor_Names) {
     print qq#<option value='$VND_ID'>$Vendor_Names{$VND_ID}</option>#;
   }

   print <<BM;   
              </select>
	    </td>
	  </tr>
          <tr>
	    <td style="border: none">
	      <label for="add_note">Note</label><br />
	    </td>
	    <td style="border: none">
              <textarea name="add_note" id="add_note2" class="text ui-corner-all" rows="3" cols="55"></textarea>
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
  my $type     = $in{'add_type'};
  my $category = $in{'add_category'};
  my $payer    = $in{'add_payer'};
  my $note     = $in{'add_note'};
  my $ph_id    = $Reverse_Pharmacy_NCPDPs{$ncpdp};
  my $date      = &build_date();
  my $date_TS   = &build_date_TS($date);

  $note =~ s/\'/\\'/g;
  $note =~ s/\"/\\"/g;

  $sql = "INSERT 
            INTO officedb.interventions (Pharmacy_ID, Type, Type_ID, Category, Program, CSR_ID, CSR_Name, Status, Opened_Date_TS, Opened_Date, Comments)
          VALUES ($ph_id, '$type', $payer, '$category', 'ReconRx', $USER, '$csr_name', 'Active', '$date_TS', '$date', '$note')"; 

#  print "SQL:\n$sql<br>\n";

  my $sthx = $dbx->prepare($sql);
  $sthx->execute() or die $DBI::errstr;
  $row_cnt = $sthx->rows;

  if ( $row_cnt != 1 ) {
    print "Insert Failed<br>";
  }
  else {
    print "Intervention Created<br>";
  }

  $sthx->finish;
}

