#______________________________________________________________________________
#
# Jay Herder
# Date: 11/10/2014
# ADMIN_PCWNR_Posting_Tool_sub.cgi
#______________________________________________________________________________

use File::Basename;
use Scalar::Util qw(looks_like_number);
use CGI;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);

if ( -e "D:/RedeemRx/MyData/RBSDesktop_routines.pl" ) {
   require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
} else {
   require "//pasrv1/RedeemRx/MyData/RBSDesktop_routines.pl";
}

$| = 1; # don't buffer output
#______________________________________________________________________________
 
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

my ($ENV) = &What_Env_am_I_in;


#####$testing++;



#####$uberdebug++;
if ($uberdebug) {
   $debug++;
   $verbose++;
#  $incdebug++;
}
#####$dbitrace++;

#______________________________________________________________________________
#	$R8DBNAME      = "ReconRxDB";
#	$R8TABLE       = "835remitstb";
#
#	$RNDBNAME      = "ReconRxDB";
#	$RNTABLE       = "PaymentNoRemit";
#
#	$PADBNAME      = "ReconRxDB";
#	$PATABLE       = "PaymentNoRemit_Archive";
 
$dbin       = "RNDBNAME";
$RNDBNAME   = $DBNAMES{"$dbin"};
$RNTABLE    = $DBTABN{"$dbin"};

$dbin       = "PADBNAME";
$PADBNAME   = $DBNAMES{"$dbin"};
$PATABLE    = $DBTABN{"$dbin"};

$dbin       = "R8DBNAME";
$R8DBNAME   = $DBNAMES{"$dbin"};
$R8TABLE    = $DBTABN{"$dbin"};

$R8DBNAME = "testing" if ( $testing );
$RNDBNAME = "testing" if ( $testing );
$PADBNAME = "testing" if ( $testing );
  
#______________________________________________________________________________

$cgi = new CGI;

for $key ( $cgi->param() ) {
   $input{$key} = $cgi->param($key);
}

print qq#Content-type: text/html\n\n#;

print "R8DBNAME: $R8DBNAME, R8TABLE: $R8TABLE\n" if ( $debug );

$USER  = $input{'USER'};
$OWNER = $input{'OWNER'};
print "USER: $USER, OWNER: $OWNER\n\n" if ($debug);

($WNCPDP, $WPharmName, $WTPP, $WCheckNumber, $WCheckAmount, $WCheckDate, $WDateAdded, $WFLAG, $WPaymentType) = split("##", $input{'WHITE'});

if ( $debug ) {
   print "WNCPDP      : $WNCPDP<br>\n";
   print "WPharmName  : $WPharmName<br>\n";
   print "WTPP        : $WTPP<br>\n";
   print "WCheckNumber: $WCheckNumber<br>\n";
   print "WCheckAmount: $WCheckAmount<br>\n";
   print "WCheckDate  : $WCheckDate<br>\n";
   print "WDateAdded  : $WDateAdded<br>\n";
#  print "WFLAG       : $WFLAG<br>\n";
   print "WPaymentType: $WPaymentType<br>\n";
}

($YNCPDP, $YCheckNumber, $YCheckAmount, $YCheckDate, $YTPP) = split("##", $input{'YELLOW'});

if ( $debug ) {
   print "YNCPDP      : $YNCPDP<br>\n";
   print "YCheckNumber: $YCheckNumber<br>\n";
   print "YCheckAmount: $YCheckAmount<br>\n";
   print "YCheckDate  : $YCheckDate<br>\n";
   print "YTPP        : $YTPP<br>\n";
}

foreach $key (sort keys %input) {
   next if ( $key =~ /WHITE|YELLOW/i );
   print "key: $key, input(): $input{$key}<br>\n<br>\n" if ($debug);
}

&UpdateDB;

#______________________________________________________________________________

my $end = time();
$elapsed = $end - $start;
print "<hr>\nTime elapsed: $elapsed seconds<hr>\n" if ($debug);

#	&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
#______________________________________________________________________________

sub UpdateDB {
  
  %attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
  $dbx = DBI->connect("DBI:mysql:$R8DBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error;
     
  DBI->trace(1) if ($dbitrace);

  $PostedBy     = "ReconRx";
  $PostedByUser = $OWNER;
  $PENDRECV     = "R";

  # Setup ability to do a RollBack if fails
  
  $sql = qq#START TRANSACTION#;
  ($rowsfound) = &ReconRx_jdo_sql($sql);

#---------------------------------------------------------------------------------------
# WHITE SECTION
#---------------------------------------------------------------------------------------
  
  if ( $debug ) {
     print "Do the WHITE Update!<br>\n";
     print "  - WNCPDP       : $WNCPDP<br>\n";
     print "  - RNDBNAME     : $RNDBNAME<br>\n";
     print "  - PADBNAME     : $PADBNAME<br>\n";
     print "  - WPharmName   : $WPharmName<br>\n";
     print "  - WTPP         : $WTPP<br>\n";
     print "  - WCheckNumber : $WCheckNumber<br>\n";
     print "  - WCheckAmount : $WCheckAmount<br>\n";
     print "  - WCheckDate   : $WCheckDate<br>\n";
     print "  - WDateAdded   : $WDateAdded<br>\n";
     print "  - WPaymentType : $WPaymentType<br>\n<br>\n";
     print "<br>\n";
  }

  $WCheckAmount =~ s/\$|,//g;

  $WHEREBLOCK  = "WHERE ";
  if ( looks_like_number($WNCPDP) ) {
     $WHEREBLOCK .= qq# NCPDP=$WNCPDP && #;
  } else {
     $WHEREBLOCK .= qq# NCPDP='$WNCPDP' && #;
  }
  $WHEREBLOCK .= "DateAdded='$WDateAdded' && ";
  $WHEREBLOCK .= "PaymentType='$WPaymentType' && ";

  if ( looks_like_number($WCheckAmount) ) {
     $WHEREBLOCK .= qq# CheckAmount=$WCheckAmount && #;
  } else {
     $WHEREBLOCK .= qq# CheckAmount='$WCheckAmount' && #;
  }

  if ( $WPaymentType !~ /EFT/i ) {
     if ( looks_like_number($WCheckNumber) ) {
        $WHEREBLOCK .= qq# CheckNumber=$WCheckNumber && #;
     } else {
        $WHEREBLOCK .= qq# CheckNumber='$WCheckNumber' && #;
     }
     if ( looks_like_number($WCheckDate) ) {
        $WHEREBLOCK .= qq# CheckDate=$WCheckDate && #;
     } else {
        $WHEREBLOCK .= qq# CheckDate='$WCheckDate' && #;
     }
  }
  $WHEREBLOCK =~ s/\&\&\s*$//g;

  $sql  = "UPDATE $RNDBNAME.$RNTABLE SET TCode='POSTED' ";
  $sql .= $WHEREBLOCK;
              
  print "sub WHITE - UPDATE sql:<br>\n$sql<br>\n" if ($debug);
  ($WHITEupdate) = &ReconRx_jdo_sql($sql);
  if ( $debug ) {
     print "WHITE - Payment No Remit updated: $WHITEupdate<br>\n";
  }
 
  # ---
  
  $sql  = "REPLACE INTO $PADBNAME.$PATABLE ";
  $sql .= "SELECT * FROM $RNDBNAME.$RNTABLE ";
  $sql .= $WHEREBLOCK;
              
  print "sub WHITE - UPDATE sql:<br>\n$sql<br>\n" if ($debug);
  ($WHITEarchive) = &ReconRx_jdo_sql($sql);
  if ( $debug ) {
     print "WHITE - Payment No Remit Lines archived: $WHITEarchive<br>\n"; 
  }

  # ---
  
  $sql  = "DELETE FROM $RNDBNAME.$RNTABLE ";
  $sql .= $WHEREBLOCK;
              
  print "sub WHITE - UPDATE sql:<br>\n$sql<br>\n" if ($debug);
  ($WHITEdelete) = &ReconRx_jdo_sql($sql);
  if ( $debug ) {
     print "WHITE - Payment No Remit deleted: $WHITEdelete<br>\n"; 
  }

#---------------------------------------------------------------------------------------
# YELLOW SECTION
#---------------------------------------------------------------------------------------

  if ( $debug ) {
     print "Do the YELLOW Update!<br>\n";
     print "  - R8DBNAME     : $R8DBNAME<br>\n";
     print "  - YNCPDP       : $YNCPDP<br>\n";
     print "  - YCheckNumber : $YCheckNumber<br>\n";
     print "  - YCheckAmount : $YCheckAmount<br>\n";
     print "  - YCheckDate   : $YCheckDate<br>\n";
     print "  - YTPP         : $YTPP<br>\n";
     print "<br>\n";
  }

  $WHEREBLOCK  = "WHERE ";
  $WHEREBLOCK .= "R_TS3_NCPDP=$YNCPDP && ";
# $WHEREBLOCK .= "R_TPP='$YTPP' && ";		# jlh. 05/06/2015. "Catamaran" will never match "SXC (Catamaran)"
# $WHEREBLOCK .= "R_BPR04_Payment_Method_Code='$YPaymentType' && ";
  $WHEREBLOCK .= "R_TRN02_Check_Number='$YCheckNumber' && ";
  $WHEREBLOCK .= "R_BPR02_Check_Amount=$YCheckAmount && ";
  $WHEREBLOCK .= "R_BPR16_Date=$YCheckDate ";

  $sql  = "UPDATE $R8DBNAME.$R8TABLE SET ";
  $sql .= "R_PENDRECV='$PENDRECV', ";
              
  #Record 'Posted By' Information
  $sql .= "R_PostedBy = '$PostedBy', ";
  $sql .= "R_PostedByUser = '$PostedByUser', ";
  $sql .= "R_PostedByDate = NOW() ";
  $sql .= $WHEREBLOCK;

  print "sub YELLOW - UPDATE sql:<br>\n$sql<br>\n" if ($debug);
  ($YELLOWupdate) = &ReconRx_jdo_sql($sql);
  if ( $debug ) {
     print "YELLOW - ReconRx 835Remits Lines updated: $YELLOWupdate<br>\n";
  }
  
#---------------------------------------------------------------------------------------

  if ( $WHITEupdate  <= 0 ||
       $WHITEarchive <= 0 ||
       $WHITEdelete  <= 0 ||
       $YELLOWupdate <= 0 ) {

     print "ROLLBACK- <br>\n";
     print "  WHITEupdate : $WHITEupdate, <br>\n";
     print "  WHITEarchive: $WHITEarchive, <br>\n";
     print "  WHITEdelete : $WHITEdelete, <br>\n";
     print "  YELLOWupdate: $YELLOWupdate <br>\n";

     $sql  = qq#ROLLBACK #;
     ($rowsfoundROLLBACK) = &ReconRx_jdo_sql($sql);
     print "<br>\nROLLBACK!!!!!!!!!!!<br>\n<br>\n" if ($debug);
     print "FAILED. Actions rolled back so database restored<br>\n";
  } else {
     $sql  = qq#COMMIT; #;
     ($rowsfound) = &ReconRx_jdo_sql($sql);
     print "COMMIT!!!!!!!!!!!<br>\n" if ($debug);
     print "Matched data has been posted/archived<br>\n";
     print "$WNCPDP ($WPharmName), $WTPP, $WCheckNumber, $WCheckAmount, $WCheckDate<br>\n";
  }

#---------------------------------------------------------------------------------------
  
  # Close the Database
  
  $dbx->disconnect;

  if ( $debug ) {
     print "sub UpdateDB: Exit.<br>\n";
  }

}

#______________________________________________________________________________
