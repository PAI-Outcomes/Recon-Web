require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;
use Date::Calc qw(Delta_Days);
use CGI;

##$CGI::POST_MAX = 1024 * 5000;

$| = 1;

my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$ret = &ReadParse(*in);
#&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

my @today = (localtime)[5,4,3];
$today[0] += 1900;
$today[1]++;

my $norepeat = int(rand(1000000000));

&readsetCookies;
&readPharmacies();

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

&readCSRs();
&read_emails();

my $query = CGI->new;
#print $q->header ( );

$inNCPDP   = $query->param('NCPDPNumber');
$all_msg   = $query->param('view_all');
$sortby    = $query->param('sortby');
$action    = $query->param('action');
$timeframe = $query->param('timeframe');
$instance  = $query->param('instance') || 0;

#$USER =  69 if ( $USER == 72);
#$PH_ID = 146 if ( $USER == 72);

$inNCPDP = substr($inNCPDP,0,7);
my $csr_name = $CSR_Reverse_ID_Lookup{$USER};

if ( $inNCPDP ) {
  $ph_id   = $Reverse_Pharmacy_NCPDPs{$inNCPDP};
}
else {
  $ph_id = $PH_ID;
  $inNCPDP = $Pharmacy_NCPDPs{$PH_ID};
}

#$ph_id = 11109;

#______________________________________________________________________________

$DBNAME   = 'ReconRxdb';

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

#print "INST: $instance ACTION: $action<br>";

if ( $instance > 0 && $action !~ /Filter/i ) {
  if ( &new_instance_chk($instance, $USER) != 1 ) {
    &add_subject() if ( $action =~ /Add/i );
    &add_reply() if ( $action =~ /Reply/i );
    &remove_msg() if ( $action =~ /Remove/i );
    &save_instance($instance, $USER);
  }
}

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  ## print qq#<script type="text/javascript" charset="utf-8" src="https://code.jquery.com/jquery-3.5.1.js"></script> \n#;
   #print '<link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/smoothness/jquery-ui.css" />';
   #print '<link rel="stylesheet" href="/css/jquery-ui.css" />';
   print '<script src="https://code.jquery.com/ui/1.13.1/jquery-ui.js"></script>';  ### This is the problem ###
   print '<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>';

   print qq#<script type="text/javascript" charset="utf-8">
           function showHideRow(row, comm_id, status) {
               var btn = "view_msg_" + comm_id;
               var disp_status = "status_" + comm_id;

               \$("\#" + row).toggle();
               if ( document.getElementById(btn).value == '+' ) {
                 if (status == 'N' ) {
                   \$.ajax("../ajax/add_message.pl", {
                      data: {
                          comm_id: comm_id,
                          action: 'View',
                          user: $USER
                      }
                   })
                   .then(
                     function success(retval) {
                         //alert('Returned status of ' + retval);
                     },

                     function fail(data, status) {
                         alert('Request failed.  Returned status of ' + status);
                     }
                   );
                 }

                 \$("\#" + btn).val('-');
                 document.getElementById(disp_status).innerHTML = "Viewed";
               }
               else {
                 \$("\#" + btn).val('+');
               }
           }

           function sort_records(col) {
              \$("\#sortby").val(col);
              \$("\#selectForm").submit();
           }

           function check_reply(comm_id, btn) {
             var elem = 'comm_' + comm_id;
             var name = 'name_' + comm_id;

             if ( document.getElementById(elem).value == '' ) {
               alert('Please enter a Message');
	       return false; 
             }

             if ( document.getElementById(name) ) {
               if ( document.getElementById(name).value == '' ) {
                 alert('Please enter your name');
  	         return false; 
               }
             }

             return true;
           }

           function add_comm(comm_id, btn) {
              var elem = 'comm_' + comm_id;
              var file = 'file_' + comm_id;
              var row  = 'Row_' + comm_id;
              var hd   = 'hidden_' + comm_id;
              var disp_status = "status_" + comm_id;

              if ( document.getElementById(elem).value == '' ) {
                alert('Please enter Message');
              }
              else {
                var comm = document.getElementById(elem).value;
                var file = document.getElementById(file).value;
                \$.ajax("../ajax/add_message.pl", {
                    data: {
                        comm_id: comm_id,
                        message: comm,
                        action: btn,
                        user: $USER
                    }
                })
                .then(
                  function success(retval) {
                    if ( retval ) {
                      \$("\#selectForm").submit();
                    }
                    else {
                      alert('Message could not be saved.' + retval);
                    }
                  },

                  function fail(data, status) {
                      alert('Request failed.  Returned status of ' + status);
                  }
                );
              }
           }

           function checkinfo(thisform, admin){
             //var thisform = 'form1';
             var message = '';
             var errors  = 0;
	     var doc = document.forms[thisform];

	     if(doc["NCPDPNumber"].value == '') {
               alert("Please filter by pharmacy to add message");
               errors++;
	     }

             if ( admin == 'N' ) {
  	       if(doc["add_name"].value == '') {
                 doc["add_name"].style.borderColor = "red";
                 errors++;
	       }
             }

	     if(doc["add_sub"].value == '') {
               doc["add_sub"].style.borderColor = "red";
               errors++;
	     }

	     if(doc["add_msg"].value == '') {
               doc["add_msg"].style.borderColor = "red";
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
		height: 320,
		width: 600,
		modal: true,
		buttons: {
			"Send": function() {
                                      var tf  = checkinfo(thisform, 'N');
					if(tf) {
					  \$('\#form1').submit();
					}
				},
			Cancel: function() {
					\$( this ).dialog( "close" );
				}
			},
			close: function() {
                                        doc["add_name"].value = '';
                                        doc["add_name"].style.borderColor = "black";
                                        doc["add_sub"].value = '';
                                        doc["add_sub"].style.borderColor = "black";
                                        doc["add_msg"].value = '';
                                        doc["add_msg"].style.borderColor = "black";
                                        doc["add_file"].value = '';
			}
		});
           });

           \$(function() {
             var thisform = 'form2';
	     var doc = document.forms[thisform];
             \$( "\#dialog-form2" ).dialog({
	  	autoOpen: false,
		height: 280,
		width: 600,
		modal: true,
		buttons: {
			"Send": function() {
                                      var tf  = checkinfo(thisform, 'Y');
					if(tf) {
					  \$('\#form2').submit();
					}
				},
			Cancel: function() {
					\$( this ).dialog( "close" );
				}
			},
			close: function() {
                                        doc["add_sub"].value = '';
                                        doc["add_sub"].style.borderColor = "black";
                                        doc["add_msg"].value = '';
                                        doc["add_msg"].style.borderColor = "black";
                                        doc["add_file"].value = '';
			}
		});
           });

           function new_communication(type) {
             if ( type == 'Admin' ) {
               \$("\#dialog-form2").dialog("open");
             }
             else {
               \$("\#dialog-form1").dialog("open");
             }
           }
         </script> \n#;

   print qq#<style>
        \#table_detail {
            background-color: \#FFFFFF;
        }

        \#table_master {
          width: 70%;
          float: left;
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
    </style>\n#;

   print qq#<!-- displayWebPage -->\n#;
 
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);

   ($PROG = $prog) =~ s/_/ /g;

   print qq#<h2>Message Account Manager</h2>\n#;
#   print "TYPE: $CSR_Types{$CSR_Reverse_ID_Lookup{$USER}}, USER: $CSR_Reverse_ID_Lookup{$USER}, $USER<br>";
   $tmp_user = '';

   if ( $ph_id ) {
     $and = "AND a.Pharmacy_ID = $ph_id";
     $tmp_user = "$ph_id";
   }
   else {
     $and = "AND c.ReconRx_Account_Manager = '$CSR_Reverse_ID_Lookup{$USER}'";
     $tmp_user = 'SELECT wlsuperuser from officedb.webloginaccess where reconrx_ram = 1';
   }

   my $months_ago = '1';

   #### Admin vs Pharmacy View
   if ( $CSR_Types{$CSR_Reverse_ID_Lookup{$USER}} =~ /Admin/i ) {
     print qq#<form id="selectForm" action="Messenger.cgi" method="post">#;
     print qq#<input type="hidden" id="sortby" name="sortby" value="">#;
     print qq#<input type="hidden" id="instance" name="instance" value="$norepeat">#;
     print qq#<table style="display: inline-block">\n#;

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

     my $sel = '';

     while ( my ($ph_id, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
       if ( $inNCPDP eq $NCPDP ) {
         $sel = 'SELECTED';
       }
       else {
         $sel = '';
       }

       print qq#<option value="$NCPDP - $Pharmacy_Name" $sel> </option>\n#;
     }

     $sthx->finish;
     
     $all_checked = '';
     if ( $all_msg ) {
       $all_checked = 'CHECKED';
     }

     $and .= " AND a.user_id NOT IN ($tmp_user)";

     $hist_30_checked = '';
     $hist_all_checked = '';

     if ( $timeframe =~ /All/i ) {
       $hist_all_sel = 'SELECTED';
       $months_ago = '12';
     }
     else {
       $hist_30_sel = 'SELECTED';
     }

     print qq#</datalist></th></tr>
              <tr><th>View:</th>
              <th>
                <span style="font-size: 12px">All Messages</span> <INPUT type="checkbox" name="view_all" value="1" $all_checked>&nbsp&nbsp
                <select name="timeframe">
                  <option value="30" $hist_30_sel>Last 30 Days</option>
                  <option value="All" $hist_all_sel>Last Year</option>
                </select>
              </th>
              </tr>
              <tr><th colspan="2"><INPUT class="button-form-xsmall" TYPE="submit" NAME="action" VALUE="Filter">&nbsp<INPUT class="button-form-xsmall" TYPE="button" VALUE="Initiate Message" onClick="new_communication('Admin')"></th></tr>
              </table>
              <div id="new_count" style="display: inline; float: right; font-size: 18px;"></div>
              </form><br>#;
   }
   else {
     my @ram = split(', ', $Pharmacy_ReconRx_Account_Managers{$ph_id});
     my $ram = "$ram[1] $ram[0]";
     my @login = split('@', $CSR_Emails{$Pharmacy_ReconRx_Account_Managers{$ph_id}});
     my $contact_email = $EMAILACCT{$login[0]};
     my $contact_phone = "(888) 255-6526 EXT: $EMAIL_SIG_EXT{$login[0]}";
     my $direct_phone = "$EMAIL_SIG_RC_PHONE{$login[0]}";

     print qq#<div style="position: relative; display: inline; float: right; font-size: 12px; white-space: nowrap;">
                <form id="selectForm" action="Messenger.cgi" method="post">
                  <IMG src="../images/RAM_$CSR_IDs{$Pharmacy_ReconRx_Account_Managers{$ph_id}}.jpg" alt="$Pharmacy_ReconRx_Account_Managers{$ph_id}" style="float: left; margin: 5px;" width="70" height="100">
                  Account Manager: $ram<br>
                  Email: $contact_email<br>
                  Phone: $contact_phone<br>
                  Direct: $direct_phone<br><br><br>
                  <INPUT class="button-form-xsmall" TYPE="button" VALUE="Message Account Manager" onClick="new_communication('Pharmacy')"><br>\n#;

     
     $ooo = &check_out_of_office($CSR_IDs{$Pharmacy_ReconRx_Account_Managers{$ph_id}});

     if ( $ooo !~ /0E0|0/i ) {
       print qq#  <span style="color: red">Out of Office and may not reply.<br>If you need immediate assistance,<br>please call (913) 897-4343.</span>#;
     }
      
     print qq#  </form>
              </div><br>#;
   }

   print qq#<table id="table_master">\n#;
   print "<thead>\n";
   print qq#<tr>
              <th><a href="javascript:sort_records('ncpdp')">NCPDP</a></th>
              <th><a href="javascript:sort_records('subject')">Subject</a></th>
              <th><a href="javascript:sort_records('dte_add')">Created</a></th>
              <th><a href="javascript:sort_records('dte_upd')">Updated</a></th>
              <th>Posts</a></th>
              <th>Status</th>
              <th>&nbsp</th>
            </tr>\n#;
   print "</thead>\n";
   print "<tbody>\n";

   my $numrowsc = 0;
   my $sql = "";

   if ( $sortby ) {
     $order = $sortby;
   }
   else {
     $order = 'mod_status, a.dte_upd DESC';
   }

   $order .= ', a.id, b.id';

   $sql = "SELECT a.id, a.user_id, a.name, a.subject, a.dte_add, a.dte_upd,
                  CASE 
                    WHEN a.user_id = $USER THEN 'X'
                    ELSE a.status
                  END AS mod_status,
                  b.user_id AS follow_user, b.message, b.attachment, b.dte_add AS dtl_add, c.ncpdp
             FROM $DBNAME.communication a
             JOIN $DBNAME.communication_dtl b ON (a.id = b.comm_id)
             JOIN officedb.pharmacy c ON (a.Pharmacy_ID = c.Pharmacy_ID)
            WHERE (a.status = 'N' OR a.dte_upd >= CURRENT_TIMESTAMP - INTERVAL $months_ago MONTH)
              $and
          ORDER BY $order";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;

#   print "SQL: $sqlout";

   $sthrp = $dbx->prepare($sql);
   $sthrp->execute();
   my $numofrows = $sthrp->rows;

   my $new_count = 0;
   my $color = '#FFFFFF';
   my $bg_color = '#133562';

   if ( $numofrows > 0 ) {
     my $inv_id_sav = 0;
     my $detail_count = 0;

     while ( my ( $comm_id, $uid, $ouser, $subject, $dte_sub_add, $dte_sub_upd, $status, $fuser, $msg, $attch, $dte_msg_add, $ncpdp) = $sthrp->fetchrow_array()) {
       if ( $comm_id != $comm_id_sav ) {
         my ($Opened_Date_Out) = &FixDBDate($dte_sub_add);
         my ($Last_Touched_Out) = &FixDBDate($dte_sub_upd);

         my @tmp_arr = split(' ', $Opened_Date_Out);
         $Opened_Date_Out = $tmp_arr[0];

         my @tmp_arr = split(' ', $Last_Touched_Out);
         $Last_Touched_Out = $tmp_arr[0];

         #### Finish Master Row
         if ( $comm_id_sav ) {
           if ( $status_sav =~ /N/i ) {
             $disp_status = 'New';
           }
           elsif ( $status_sav =~ /X/i ) {
             $disp_status = 'Sent';
           }
           else {
             $disp_status = 'Viewed';
           }

           print qq#<td style="text-align: center; width: 50px;">$detail_count</td>\n#;
           print qq#<td style="text-align: center; width: 50px;"><div id="status_$comm_id_sav">$disp_status</div></td>\n#;
           print qq#<td nowrap style="text-align: center; width: 50px;"><input type="button" name="view_msg_$comm_id_sav" id="view_msg_$comm_id_sav" value="+" onClick="javascript:showHideRow('hidden_$comm_id_sav', $comm_id_sav, '$status_sav')"></td>\n#;
           print qq#</tr>\n#;

           #### Add Detail Rows
           print qq#<tr id="hidden_$comm_id_sav" class="hidden_row" style="border: solid \#133562 2px"><td colspan=7><table id="table_detail" style="width: 100%">$hidden_rows#;

           print qq#<tr style="border: none;">
                      <td colspan=3>
                        <form action="Messenger.cgi" method="post" enctype="multipart/form-data">
                          <input type="hidden" name="comm_id" value="$comm_id_sav">
                          <input type="hidden" name="view_all" value="$all_msg">
                          <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
                    <input type="hidden" name="instance" value="$norepeat">
                          <input type="hidden" name="timeframe" value="$timeframe">#;

           if (! $CSR_Reverse_ID_Lookup{$USER} ) {
             print qq#    Name: <input type="text" id="name_$comm_id_sav" name="add_name" value="$ouser_sav" size="45"><br>#;
           }

           print qq#      Reply:<br>
                          <textarea id="comm_$comm_id_sav" name="add_msg" rows="4" cols="100%"></textarea><br>
                          Attachment: <input type="file" id='file_$comm_id_sav' name="add_file">
                          <div style="text-align: right">
                            <input type='submit' class="button-form-xsmall" name='action' value='Reply' onClick="return check_reply($comm_id_sav, this.value)">#;

           if ( $CSR_Reverse_ID_Lookup{$USER} ) {
             print qq#<input type='submit' class="button-form-xsmall" name='action' value='Remove'">#;
           }

           print qq#      </div>
                        </form>
                      </td></tr>\n#;

           print qq#</table></td></tr>\n#;
         }

         print qq#<tr id="Row_$comm_id" style="background-color: $bg_color; color: $color; border-right: solid \#133562 2px; border-left: solid \#133562 2px">\n#;
         print qq#<td nowrap style="width: 80px;">$ncpdp</td>\n#;
         print qq#<td>$subject</td>\n#;
         print qq#<td nowrap style="width: 100px;">$Opened_Date_Out</td>\n#;
         print qq#<td nowrap style="width: 100px;">$Last_Touched_Out</td>\n#;

         $detail_count = 0;
         $hidden_rows = '';
         $new_count++ if ( $status =~ /N/i );
       }

       if ( $CSR_Reverse_ID_Lookup{$fuser} ) {
         my @ram = split(', ', $CSR_Reverse_ID_Lookup{$fuser});
         $disp_name = "$ram[1] $ram[0]";
       }
       else {
         $disp_name = $ouser;
       }

       #### Build Detail Rows
       my ($Follow_Up_Date) = &FixDBDate($dte_msg_add);

       $hidden_rows .= qq#<tr style="border: none;">
                            <td nowrap style="width: 200px; font-size: 11px">$disp_name<br>$Follow_Up_Date</td>
                            <td style="vertical-align: text-top;">$msg</td>#;

       if ( $attch ) {
         $attch = "../Webshare/uploads/$attch";
         $hidden_rows .= qq#<td nowrap style="width: 100px; vertical-align: text-top;"><a href="$attch">Attachment</a></td>#;
       }
       else {
         $hidden_rows .= qq#<td nowrap style="width: 100px; vertical-align: text-top;">&nbsp</td>#;
       }

       $hidden_rows .= qq#</tr>\n#;
       ++$detail_count;

       $comm_id_sav = $comm_id;
       $status_sav = $status;
       $uid_sav = $uid;
       $ouser_sav = $ouser;
     }

     #### Finish Last Record
     if ( $status_sav =~ /N/i ) {
       $disp_status = 'New';
     }
     elsif ( $status_sav =~ /X/i ) {
       $disp_status = 'Sent';
     }
     else {
       $disp_status = 'Viewed';
     }

     print qq#<td style="text-align: center; width: 50px;">$detail_count</td>\n#;
     print qq#<td style="text-align: center; width: 50px;"><div id="status_$comm_id_sav">$disp_status</div></td>\n#;
     print qq#<td nowrap style="text-align: center; width: 50px;"><input type="button" name="view_msg_$comm_id_sav" id="view_msg_$comm_id_sav" value="+" onClick="javascript:showHideRow('hidden_$comm_id_sav', $comm_id_sav, '$status_sav')"></td>\n#;

     print qq#</tr>\n#;

     #### Finishing Detail Rows
     print qq#<tr id="hidden_$comm_id_sav" class="hidden_row" style="border: solid \#133562 1px"><td colspan=7><table id="table_detail" style="width: 100%">$hidden_rows#;

     print qq#<tr style="border: none;">
                <td colspan=3>
                  <form action="Messenger.cgi" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="comm_id" value="$comm_id_sav">
                    <input type="hidden" name="view_all" value="$all_msg">
                    <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
                    <input type="hidden" name="instance" value="$norepeat">
                    <input type="hidden" name="timeframe" value="$timeframe">#;

     if (! $CSR_Reverse_ID_Lookup{$USER} ) {
       print qq#    Name: <input type="text" id="name_$comm_id_sav" name="add_name" value="$ouser_sav" size="45"><br>#;
     }

     print qq#      Reply:<br>
                    <textarea id="comm_$comm_id_sav" name="add_msg" rows="4" cols="100%"></textarea><br>
                    Attachment: <input type="file" id='file_$comm_id_sav' name="add_file">
                    <div style="text-align: right">
                    <input type='submit' class="button-form-xsmall" name='action' value='Reply' onClick="return check_reply($comm_id_sav, this.value)">#;

     if ( $CSR_Reverse_ID_Lookup{$USER} ) {
       print qq#<input type='submit' class="button-form-xsmall" name='action' value='Remove'">#;
     }

     print qq#      </div>
                  </form>
                </td></tr>\n#;

     print qq#</table></td></tr>\n#;
   }
   else {
     print qq#<tr style="background-color: $bg_color; color: $color; border-right: solid \#133562 2px; border-left: solid \#133562 2px"><td colspan=7>No New Messages</td></tr>#;
   }

   $sthrp->finish;
 
   print qq#</tbody>\n#;
   print qq#</table>\n#;

   #### Insert Number of New Messages
   if ( $CSR_Reverse_ID_Lookup{$USER} ) {
     print qq#<script type="text/javascript" charset="utf-8">
                   document.getElementById("new_count").innerHTML = "New Messages: $new_count";
               </script>#;
   }
   #######

   #### Hidden Input Form1
   print qq#<div id="dialog-form1" title="Add Topic" style="display: none;">
       <form id="form1" action="Messenger.cgi" method="post" enctype="multipart/form-data">
         <input type="hidden" name="action" value="Add">
         <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
         <input type="hidden" name="view_all" value="$all_msg">
         <input type="hidden" name="sortby" value="$sortby">
         <input type="hidden" name="instance" value="$norepeat">
         <input type="hidden" name="timeframe" value="$timeframe">

         <table class="tableNoBorder">
           <tr style="border: none">
               <td style="border: none">
  	       <label for="add_name">Name</label>
	     </td>
	     <td style="border: none">
               <input type="text" name="add_name" id="add_name" size="45">
	     </td>
	   </tr>
           <tr style="border: none">
 	     <td style="border: none">
 	       <label for="add_sub">Subject</label>
	     </td>
	     <td style="border: none">
               <input type="text" name="add_sub" id="add_sub" size="45">
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	      <label for="add_msg">Message</label>
	     </td>
	     <td style="border: none">
              <textarea id="add_msg" name="add_msg" class="text ui-corner-all" rows="3" cols="46"></textarea>
	     </td>
           </tr>
	   <tr style="border: none">
	     <td nowrap style="border: none">
              <label for="add_file">Attachment</label>
             </td>
	     <td style="border: none">
              <input type="file" id='add_file' name="add_file">
             </td>
           </tr>
 	 </table>
      </form>
    </div>#;

   #### Hidden Input Form2
   print qq#<div id="dialog-form2" title="Add Topic" style="display: none;">
       <form id="form2" action="Messenger.cgi" method="post" enctype="multipart/form-data">
         <input type="hidden" name="action" value="Add">
         <input type="hidden" name="NCPDPNumber" value="$inNCPDP">
         <input type="hidden" name="view_all" value="$all_msg">
         <input type="hidden" name="sortby" value="$sortby">
         <input type="hidden" name="instance" value="$norepeat">
         <input type="hidden" name="timeframe" value="$timeframe">

         <table class="tableNoBorder">
           <tr style="border: none">
 	     <td style="border: none">
 	       <label for="add_sub">Subject</label>
	     </td>
	     <td style="border: none">
               <input type="text" name="add_sub" id="add_sub" size="45">
	     </td>
	   </tr>
	   <tr style="border: none">
	     <td style="border: none">
	      <label for="add_msg">Message</label>
	     </td>
	     <td style="border: none">
              <textarea id="add_msg" name="add_msg" class="text ui-corner-all" rows="3" cols="46"></textarea>
	     </td>
           </tr>
	   <tr style="border: none">
	     <td nowrap style="border: none">
              <label for="add_file">Attachment</label>
             </td>
	     <td style="border: none">
              <input type="file" id='add_file' name="add_file">
             </td>
           </tr>
 	 </table>
      </form>
    </div>#;
}

#______________________________________________________________________________

sub add_subject {
  my $name     = $query->param('add_name');
  my $subject  = $query->param('add_sub');
  my $message  = $query->param('add_msg');
  my $file     = $query->param('add_file');
  my $comm_id  = 0;

  $subject =~ s/\'/\\'/g;
  $subject =~ s/\"/\\"/g;
  $message =~ s/\'/\\'/g;
  $message =~ s/\"/\\"/g;

  $sql = "INSERT INTO reconrxdb.communication (pharmacy_id, user_id, `name`, subject, status)
          VALUES ($ph_id, $USER, '$name', '$subject', 'N')";

#  print "SQL:\n$sql<br>\n";

  $inserted = $dbx->do($sql) or die $DBI::errstr;

  if ( $inserted != 1 ) {
    print "INSERT Failed\n";
  }
  else {
    $sth = $dbx->prepare("SELECT LAST_INSERT_ID()") || die "Error preparing query" . $dbx->errstr;
    $sth->execute() or die $DBI::errstr;
    $comm_id = $sth->fetchrow_array();
    $sth->finish();
  }

  ### Save file, if provided
  if ( $file !~ /^\s*$/ && $comm_id ) {
    ($retval, $location) = &save_file($comm_id);
  }
  else {
    $retval = 1;
    $location = '';
  }

  if ( $retval ) {
    $sql = "INSERT INTO reconrxdb.communication_dtl (comm_id, user_id, status, message, attachment)
            VALUES ($comm_id, $USER, 'N', '$message', '$location')"; 

#    print "SQL:\n$sql<br>\n";

    $inserted = $dbx->do($sql) or die $DBI::errstr;

    if ( $inserted != 1 ) {
      print "Insert Failed<br>";
    }
    else {
      print "Message Added<br>";
    }
  }
  else {
    $sql = "DELETE FROM reconrxdb.communication WHERE id = $comm_id";
    $dbx->do($sql) or die $DBI::errstr;
  }
}

sub add_reply {
  my $comm_id  = $query->param('comm_id');
  my $name     = $query->param('add_name');
  my $message  = $query->param('add_msg');
  my $file     = $query->param('add_file');

  my $sql;
  my $row_cnt;
  my $upd_name = '';
  $message =~ s/\'/\\'/g;
  $message =~ s/\"/\\"/g;

  ### Save file, if provided
  if ( $file !~ /^\s*$/ && $comm_id ) {
    ($retval, $location) = &save_file($comm_id);
  }
  else {
    $retval = 1;
    $location = '';
  }

  if ( $retval ) {
    $sql = "INSERT INTO reconrxdb.communication_dtl (comm_id, user_id, message, attachment)
            VALUES ($comm_id, $USER, '$message', '$location')"; 

#    print "SQL:\n$sql\n\n" ;
    $row_cnt = $dbx->do($sql) or die $DBI::errstr;

    if ( $row_cnt != 1 ) {
      $row_cnt = 0;
    }

    if ( $name !~ /^\s*$/ ) {
      $upd_name = " name = '$name', ";
    }

    $sql = "UPDATE reconrxdb.communication
               SET user_id = $USER,
                   $upd_name
  	           status  = 'N',
  	  	   dte_upd = CURRENT_TIMESTAMP
             WHERE id = $comm_id";

#    print "SQL:\n$sql\n\n" ;
    $dbx->do($sql) or die $DBI::errstr;
  }
}

sub remove_msg {
  my $comm_id  = $query->param('comm_id');

  my $sql;
  my $row_cnt;
  my $upd_name = '';

  $sql = "UPDATE reconrxdb.communication
             SET user_id = $USER
           WHERE id = $comm_id";

#  print "SQL:\n$sql\n\n" ;
  $dbx->do($sql) or die $DBI::errstr;
}


sub save_file {
  my $comm_id = shift @_;
  my $safe_filename_characters = "a-zA-Z0-9_.-";

  my $filename = $query->param("add_file");

  my $newfilename = "${comm_id}_${filename}";

  if ( !$filename ) {
    print "There was a problem uploading your file (try a smaller file).";
    return(0);
  }

  my ( $name, $path, $extension ) = fileparse ( $filename, '..*' );
  $filename = $name . $extension;
  $filename =~ tr/ /_/;
  $filename =~ s/[^$safe_filename_characters]//g;
  
  if ( $filename =~ /^([$safe_filename_characters]+)$/ ) {
    $filename = $1;
  }
  else {
    print "Filename contains invalid characters";
    return(0);
  }

  my $UPLOAD_FH = $query->upload("add_file");

  my $newfilename = "${comm_id}_${filename}";

  umask 0000; #This is needed to ensure permission in new file
  my $upload_dir = "D:\\WWW\\members.recon-rx.com\\WebShare\\uploads";

  open $NEWFILE_FH, ">$upload_dir\\$newfilename" or die "Could not open file for writing: $upload_dir\\$newfilename - $!<br>";

  if ($filename =~ /\.zip|\.pdf|\.xlxs|\.xls/) {
    binmode $NEWFILE_FH;
  }

  while ( <$UPLOAD_FH> ) {
    print $NEWFILE_FH "$_";
  }

  close $NEWFILE_FH or die "I cannot close filehandle: $!";

  return(1, $newfilename);
}

sub check_out_of_office {
  my $user_id = shift @_;

  $sql = "SELECT id
            FROM officedb.holiday_pto_schedule
           WHERE ((user_id = $user_id AND type = 'P')
                 OR (type = 'H')) 
             AND dte = CURRENT_DATE";

#    print "SQL:\n$sql\n\n" ;
  $pto_day = $dbx->do($sql) or die $DBI::errstr;

  return($pto_day)
}

sub new_instance_chk {
  my $id = shift @_;
  my $user_id = shift @_;
  my $retval;

  $sql = "SELECT 1
            FROM reconrxdb.communication_inst
           WHERE id = $id
             AND user_id = $user_id";

#    print "SQL:\n$sql\n\n" ;
  $retval = $dbx->do($sql) or die $DBI::errstr;

#  print "RETVAL: $retval<br>";

  return($retval);
}

sub save_instance {
  my $id = shift @_;
  my $user_id = shift @_;
  my $retval;

  $sql = "INSERT INTO reconrxdb.communication_inst (id, user_id)
          VALUES ($id, $user_id)";

#    print "SQL:\n$sql\n\n" ;
  $dbx->do($sql) or die $DBI::errstr;
}
