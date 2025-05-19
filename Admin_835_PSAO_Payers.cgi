use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";
my $AddRemove;
my $AR_ID;

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
    &MyReconRxHeader;
    &ReconRxHeaderBlock;
} else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  exit(0);
}

#______________________________________________________________________________

&hasAccess($USER);


#______________________________________________________________________________

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$adate  = sprintf("%04d-%02d-%02d", $year, $month, $day);

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#Start page operations
$PSAO_ID = 0; 
$PSAO_ID = $in{PSAO_ID} if ($in{PSAO_ID}); 
$AR_ID = $in{ar_id} if ($in{ar_id}); 

$AddRemove = $in{AddRemove} if ($in{AddRemove}); 
&update_table if($AddRemove);

&displayOptions;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub update_table {

  my $DBNAME = "reconrxdb";
 ## my $TABLE  = "psao_payer_dtl";
  my $TABLE  = "other_sources_835s_lookup";
  my $change;

  if ($AddRemove eq 'Remove' && $PSAO_ID && $AR_ID) {
    $sql = "DELETE
              FROM $DBNAME.$TABLE 
             WHERE Lookup_Other_Source_TPP_ID = $PSAO_ID 
                && Lookup_TPP_Display_on_Remit_TPP_ID = $AR_ID
           ";
    $change = 1;
  
  }
  if ($AddRemove eq 'Add' && $PSAO_ID && $AR_ID) {
     $psao_ctl = 0;
    if($PSAO_ID == 700470) {
      $sql = " SELECT R_REF02_Value from 835remitstb
                WHERE R_TPP_PRI = 700470
                   && R_REF02_Value LIKE concat('%',(SELECT Third_Party_Payer_Name FROM officedb.third_party_payers where Third_Party_Payer_ID = $AR_ID), '%')
                   LIMIT 1
             ";
      my $sth  = $dbx->prepare("$sql");
      $sth->execute;
      ($lookupBin) = $sth->fetchrow_array();
      if ($dbx->rows <=0) {
        $lookupBin = 'NA';
        $psao_ctl = $AR_ID;
      }
    }
    $sql = "INSERT INTO $DBNAME.$TABLE (Lookup_Other_Source_TPP_ID, Lookup_BIN_REF, Lookup_TPP_Display_on_Remit_TPP_ID, Lookup_TPP_Display_on_Remit, PSAO_Control) 
             SELECT $PSAO_ID,'$lookupBin',$AR_ID, Third_Party_Payer_Name, $psao_ctl FROM officedb.third_party_payers where third_party_payer_id =  $AR_ID; 
           ";
    $change = 1;
  }

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute if($change == 1);

}
 
sub displayOptions {
  print "<hr>\n";

  print qq#<style> \n#;
  print qq#td { border-top: none; }\n#;
  print qq#</style> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# function AddRemove(act) { \n#;
  print qq# var alt1 = "Are you sure that you want to "\n#;
  print qq# alt1 += act\n#;
  print qq# alt1 += ' '\n#;
  print qq# if(act == 'Add') { var val =\$("\#AddTpp :selected").val(); var alt2 =  \$("\#AddTpp :selected").text();} else {var val =\$("\#RemoveTpp :selected").val(); var alt2 =  \$("\#RemoveTpp :selected").text();}\n#;
  print qq# var alt3 = alt1.concat(alt2)\n#;
  print qq#   if (confirm(alt3)) { document.getElementById('AddRemove').value = act; document.getElementById('ar_id').value = val; document.getElementById('selectForm').submit();}else {} \n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#<form id="selectForm" action="$PROG" method="post" >#;
  print "<table>\n";

  print qq#<tr><td><label for="PH_ID">PSAO:</label></td>#;
  print qq#<td><label for="TPP_ID">Third Party Payer:</label></td></tr>#;
  print qq#<tr><td><select onchange='this.form.submit();' name="PSAO_ID" id="psao_id" style="width:450px;" >\n#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  &readCSRs();
  $ram = $CSR_Reverse_ID_Lookup{$USER};

  my $sql = "SELECT psao_id,  PSAO_Name
               FROM reconrxdb.psao_ref
             WHERE PSAO_primary
           ORDER BY PSAO_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  $select = '';
  $select = 'selected="selected"' if ($PSAO_ID == $ID);
  print qq#<option style="display:none" value="0" $select>Please select a PSAO</option>\n#;
  while ( my ($ID, $PSAO_Name) = $sthx->fetchrow_array() ) {
    $select = '';
    $select = 'selected="selected"' if ($PSAO_ID == $ID);
    print qq#<option value="$ID" $select>$PSAO_Name</option>\n#;
  }

  $sthx->finish;
  print qq# </select></td>#;

  print qq#<td><select name="TPP" id="Tpp" size="20" multiple style="width:450px;">\n#;

  my $DBNAME = "reconrxdb";
  ##my $TABLE  = "psao_payer_dtl";
  my $TABLE  = "other_sources_835s_lookup";

  $sql = "SELECT lookup_tpp_display_on_Remit_TPP_ID, Lookup_TPP_Display_on_Remit
            FROM $DBNAME.$TABLE 
           WHERE Lookup_other_source_tpp_id = $PSAO_ID 
        ORDER BY Lookup_TPP_Display_on_Remit";

  my $sthx  = $dbx->prepare("$sql");
##print $sql;
  $sthx->execute;

  while ( my ($TPP_ID, $TPP_NAME) = $sthx->fetchrow_array() ) {
    push (@tpp_ids, $TPP_ID);
    push (@tpp, "$TPP_ID:$TPP_NAME");
    print qq#<option value="$TPP_ID">$TPP_ID - $TPP_NAME</option>\n#;
  }

  $sthx->finish;
  print qq# </select></td></tr>#;


  print qq#</table>\n#;

  print qq#<input type="hidden" name="AddRemove" id="AddRemove">\n#;
  print qq#<input type="hidden" name="ar_id" id="ar_id">\n#;

  print qq#</form>\n#;

  print qq#<br /><hr />\n#;
  ##if ($PSAO_ID && $PAI_TPP_Edit =~ /^Yes/i ) {
  if ($PSAO_ID && $USER =~ /^69$|^66$|^73$/i ) {
    print qq#<form id="addForm" action="$PROG" method="post" >#;
    print qq#<input type="hidden" name="PSAO_ID" value="$PSAO_ID">\n#;
    print "<table>\n";
    print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="AddPayer" VALUE="Add Payer"onclick="AddRemove('Add');"></td>\n#;
  
    print qq#<td><select name="TPP_ID" id="AddTpp" style="width:450px;">\n#;
  
    my $DBNAME = "officedb";
    my $TABLE  = "third_party_payers";
    my $tpp_s  = join(',', @tpp_ids);
  
    $sql = "SELECT Third_Party_Payer_ID, Third_Party_Payer_Name, BIN
              FROM $DBNAME.$TABLE 
             WHERE primary_secondary = 'Pri'
                && status = 'Active' 
                && Third_Party_Payer_ID NOT IN ($tpp_s)
          ORDER BY Third_Party_Payer_Name";
  
    my $sthx  = $dbx->prepare("$sql");
    $sthx->execute;
  
    while ( my ($TPP_ID, $TPP_NAME, $BIN) = $sthx->fetchrow_array() ) {
      print qq#<option value="$TPP_ID">$TPP_ID-$BIN - $TPP_NAME</option>\n#;
    }
  
    print qq# </select></td></tr>#;
    print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="RemovePayer" VALUE="Remove Payer" onclick="AddRemove('Remove');"></td>\n#;
    print qq#<td><select name="RemoveTPP" id="RemoveTpp" style="width:450px;">\n#;
    foreach $payer (@tpp) {
      ($TPP_ID,$TPP_NAME) = split(/:/,$payer);
      print qq#<option value="$TPP_ID">$TPP_ID - $TPP_NAME</option>\n#;
    }
    print qq# </select></td></tr>#;
    print qq#</table>\n#;
    print qq#</form>\n#;
  }
}
