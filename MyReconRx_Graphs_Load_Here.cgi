#______________________________________________________________________________
#
# Jay Herder
# Date: 05/14/2012
# Mods: 08/02/2012
# Mods: 01/04/2013. Major mods
# MyReconRx.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
# $incdebug++;
  $debug++;
  $verbose++;
}
#####$dbitrace++;
#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$debug   = $in{'debug'}   if (!$debug);
$verbose = $in{'verbose'} if (!$verbose);

$debug++ if ( $verbose );

$WHICHDB    = $in{'WHICHDB'};

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$RUSER      = $in{'RUSER'};
$RPASS      = $in{'RPASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$isMember   = $in{'isMember'};
$CUSTOMERID = $in{'CUSTOMERID'};
$LTYPE      = $in{'LTYPE'};
$OLTYPE     = $in{'OLTYPE'};
$LDATEADDED = $in{'LDATEADDED'};
$inTPP      = $in{'inTPP'};
$inBIN      = $in{'inBIN'};
$inBINP     = $in{'inBINP'};
$OWNER      = $in{'OWNER'};
$OWNERPASS  = $in{'OWNERPASS'};

$inPharmacy = $in{'inPharmacy'};
$inNPI      = $in{'inNPI'};
$inNCPDP    = $in{'inNCPDP'};
$dispNPI    = $in{'dispNPI'};
$dispNCPDP  = $in{'dispNCPDP'};

$SAVEVALID = $VALID;

($WHICHDB)  = &StripJunk($WHICHDB);
($USER)     = &StripJunk($USER);
($PASS)     = &StripJunk($PASS);
($RUSER)    = &StripJunk($RUSER);
($RPASS)    = &StripJunk($RPASS);

($inNPI)    = &StripJunk($inNPI);
($inNCPDP)  = &StripJunk($inNCPDP);
($dispNPI)  = &StripJunk($dispNPI);
($dispNCPDP)= &StripJunk($dispNCPDP);

$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";
$CUSTOMERID = "" if ( !$CUSTOMERID );



# $USER = $RUSER if ( !$USER && $RUSER );
# $PASS = $RPASS if ( !$PASS && $RPASS );
if ( $USER eq "" ) {
   $USER = $RUSER;
   $PASS = $RPASS;
}

#	# if all integer, fix to be full 7/10 long with leading zeros!
#	if ( $USER !~ m/[^0-9.]/ ) {
#	   $USER = substr("0000000"    . $USER, -7);
#	   $PASS = substr("0000000000" . $PASS, -10);
#	}

my @NCPDParray = ();

&readsetCookies;

#______________________________________________________________________________
# &readLogins;
# ($isMember, $VALID) = &isReconRxMember($USER, $PASS);

if ( $USER =~ /\@/ ) {
   $RUSER = "";
   $RPASS = "";
}

if ( $USER ) {
   $inNCPDP   = $USER;
   $dispNCPDP = $USER;
} else {
   $inNCPDP   = $in{'inNCPDP'};
   $dispNCPDP = $in{'dispNCPDP'};
}
if ( $PASS ) {
   $inNPI   = $PASS;
   $dispNPI = $PASS;
} else {
   $inNPI   = $in{'inNPI'};
   $dispNPI = $in{'dispNPI'};
}

$UpDB_NCPDP = $in{"UpDB_NCPDP"};
$UpDB_NPI   = $in{"UpDB_NPI"};
if ( $UpDB_NCPDP && $UpDB_NCPDP !~ /^\s*$/ ) {
   $RUSER = $UpDB_NCPDP;
   $RPASS = $Pharmacy_NPIs{$RUSER};
   $USER  = $RUSER;
   $PASS  = $RPASS;
}
if ( $UpDB_NPI && $UpDB_NPI !~ /^\s*$/ ) {
   $RUSER = $Reverse_Pharmacy_NPIs{$UpDB_NPI};
   $RPASS = $UpDB_NPI;
   $USER  = $RUSER;
   $PASS  = $RPASS;
}

if ( !$USER && $RUSER ) {
   $USER = $RUSER;
   $PASS = $RPASS;
}
if ( !$RUSER && $USER ) {
   $RUSER = $USER;
   $RPASS = $PASS;
}

($isMember, $VALID) = &isReconRxMember($USER, $PASS);




$gizmo = -99;
$saveRUSER  = $RUSER;
$saveOLTYPE = $OLTYPE;

if ( $RUSER =~ /\@/ && $OLTYPE =~ /^SuperUser|^Owner$|^Admin$/i ) {

   my $USER    = "";
   my $PASS    = "";
   my $RUSER   = "";
   my $RPASS   = "";
   my $OWNER      = "";
   my $OWNERPASS  = "";

   $gizmo = 24;
   
   if ( $USER !~ /^\s*$/ ) {
      print qq#Set-Cookie:USER=$USER;             path=/; domain=$cookie_server;\n#;
   }
   if ( $PASS !~ /^\s*$/ ) {
      print qq#Set-Cookie:PASS=$PASS;             path=/; domain=$cookie_server;\n#;
   }
   print qq#Set-Cookie:RUSER=$RUSER;           path=/; domain=$cookie_server;\n#;
   print qq#Set-Cookie:RPASS=$RPASS;           path=/; domain=$cookie_server;\n#;
   print qq#Set-Cookie:OWNER=$OWNER;           path=/; domain=$cookie_server;\n#;
   print qq#Set-Cookie:OWNERPASS=$OWNERPASS;   path=/; domain=$cookie_server;\n#;

}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);
#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);		# Moved up a bit...

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;
#  print "1. isMember: $isMember, VALID: $VALID<hr>\n";
#  print "1. USER: $USER<br>RUSER: $RUSER<br>OWNER: $OWNER<br>OLTYPE: $OLTYPE<br>\n" if ($debug);

} else {

#  print "2. USER: $USER<br>RUSER: $RUSER<br>OWNER: $OWNER<br>OLTYPE: $OLTYPE, LTYPE: $LTYPE, isMember: $isMember, VALID: $VALID<br>\n" if ($debug);
#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;

   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

&readPharmacies;

### Log pharmacy login

print "SAVEVALID: $SAVEVALID, USER: $USER, OWNER: $OWNER<br>\n" if ($debug);
if ( $SAVEVALID =~ /^\s*$|$RxAdmin/ ) {
   print "USER: $USER, OWNER: $OWNER<br>\n" if ($debug);
   if ( $USER !~ m/[^0-9.]/ && $USER > 0 && $OWNER !~ /pharmassess/i) {
      $Pharmacy_Name = $Pharmacy_Names{$USER};
      &logActivity($Pharmacy_Name, "Logged in to ReconRx", $USER);
   } else {
      if ( $USER eq $OWNER ) {
         &logActivity($RUSER, "SuperUser Logged in to ReconRx", NULL);
      }
   }
}

#______________________________________________________________________________

print "<hr size=8 noshade color=green>gizmo: $gizmo, RUSER: $RUSER OLTYPE: $OLTYPE, saveRUSER: $saveRUSER, saveOLTYPE: $saveOLTYPE<hr>\n" if ($debug);
print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
   print "<br>isAdmin: $isAdmin<br>\n";
   print "dol0: $0<br>\n";
   print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
   print "<hr size=4 noshade color=blue>\n";
   print "PROG: $PROG<br>\n";
   print "<br>\n";
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
   my $key;
   foreach $key (sort keys %in) {
#     next if ( $key =~ /PASS/i );
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
#  print "inNPI: $inNPI, dispNPI: $dispNPI<br>\n";
#  print "inNCPDP: $inNCPDP, dispNCPDP: $dispNCPDP<br>\n";
   print "WHICHDB: $WHICHDB<br>\n";
   print "<hr size=4 noshade color=blue>\n";
}

#______________________________________________________________________________

#&displayPharmacyRight($USER, $PASS) if ( $RUSER !~ /\@/ );

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

print "0. USER: $USER<br>RUSER: $RUSER<br>OWNER: $OWNER<br>OLTYPE: $OLTYPE<br>\n" if ($debug);

&read_this_Owners_Pharmacies($RUSER, $OLTYPE);

&displayWebPage;
&displayPharmacyRight($USER, $PASS) if ( $RUSER !~ /\@/ );

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

   print qq#<!-- displayWebPage -->\n#;
   print "sub displayWebPage: Entry.<br>\n" if ($debug);
 
   print "1. USER: $USER<br>RUSER: $RUSER<br>OWNER: $OWNER<br>OLTYPE: $OLTYPE<br>\n" if ($debug);

   #print qq#<div id="textarea2" style="padding-bottom:40px;" class="notices">\n#;

   if ( $debug ) {
      print "inNPI    : $inNPI<br>\n";
      print "dispNPI  : $dispNPI<br>\n";
      print "inNCPDP  : $inNCPDP<br>\n";
      print "dispNCPDP: $dispNCPDP<br>\n";
      print "USER     : $USER<br>\n";
      print "PASS     : $PASS<br>\n";
   }

   $form_inNPI   = $inNPI   || $dispNPI;
   $form_inNCPDP = $inNCPDP || $dispNCPDP;

   $FMT = "%0.02f";
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
#  print "date: $date, DATE: $DATE, SFDATE: $SFDATE, SFDATE2: $SFDATE2<br>\n" if ($debug);
 
   ($PROG = $prog) =~ s/_/ /g;

   &process_notifications;

   if ( $RUSER =~ /\@/ ) {
   } elsif ( $RUSER =~ /^\s*$/ ) {
   } else {
   
      if ( $inPharmacyName ) {
         print qq#<tr><th colspan=3 align=center><font size=+1><i>$inPharmacyName</i></font></th></tr>\n#;
      }

      # if ( $WHICHDB =~ /^Webinar$/i ) {

         # &Print_Canned_At_a_Glance;

      # } else {

         # &Print_Once_Daily_At_a_Glance;
      # }
   }

   if ( $VALID && $RUSER =~ /\@/ && $OLTYPE =~ /^SuperUser|^Owner$|^Admin$/i ) {

#     $URLH = "${prog}.cgi";

      print qq#<h2>Pharmacy Selection</h2>\n#;
      print qq#<p>Please select the pharmacy you wish to view from the list below:</p>\n#;
    
   print "2. USER: $USER<br>RUSER: $RUSER<br>OWNER: $OWNER<br>OLTYPE: $OLTYPE<br>\n" if ($debug);
      if ( $OWNER =~ /\@/ ) {
           # okay
      } elsif ( $RUSER =~ /\@/ ) {
           $OWNER     = $RUSER;
           $OWNERPASS = $RPASS;
      } elsif ( $USER =~ /\@/ ) {
           $OWNER     = $USER;
           $OWNERPASS = $PASS;
      }

      if ( $OLTYPE =~ /^Admin$|^SuperUser$/i ) {

         print qq#<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>\n#;
         print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
         print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
         print qq#<script type="text/javascript" charset="utf-8"> \n#;
         print qq#\$(document).ready(function() { \n#;
         print qq#                \$('\#tablef').dataTable( { \n#;
         print qq#                                "sScrollX": "100%", \n#;
         print qq#                                "bScrollCollapse": true,  \n#;
         print qq#                                "sScrollY": "350px", \n#;
         print qq#                                "bPaginate": false \n#;
         print qq#                } ); \n#;
         print qq#} ); \n#;
         print qq#</script> \n#;
#
         print qq#<table id="tablef">\n#;
         print "<thead>";
         print "<tr><th>$nbsp</th><th>Pharmacy Name</th><th>NCPDP</th><th>NPI</th><th>Phone</th><th>Address</th></tr>";
         print "</thead>";
         print "<tbody>";

         foreach $ONCPDP (sort { $OPharmacy_Names{$a} cmp $OPharmacy_Names{$b} } keys %ONCPDPs) {

            $OPharmacy_Name = $OPharmacy_Names{$ONCPDP};

            print "<tr>";
            print qq#<td>#;
            $URLH = "MyReconRx.cgi";
            print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
            print qq#<INPUT TYPE="hidden" NAME="debug"   VALUE="$debug">\n#;
            print qq#<INPUT TYPE="hidden" NAME="verbose" VALUE="$verbose">\n#;
            print qq#<INPUT TYPE="hidden" NAME="VALID"   VALUE="$VALID">\n#;
            print qq#<INPUT TYPE="hidden" NAME="isOWNER" VALUE="$isOWNER">\n#;
            print qq#<INPUT TYPE="hidden" NAME="OWNER"   VALUE="$OWNER">\n#;
            print qq#<INPUT TYPE="hidden" NAME="OWNERPASS" VALUE="$OWNERPASS">\n#;
            print qq#<INPUT TYPE="hidden" NAME="USER"    VALUE="$ONCPDP">\n#;
            print qq#<INPUT TYPE="hidden" NAME="PASS"    VALUE="$ONPIs{$ONCPDP}">\n#;
            print qq#<INPUT TYPE="hidden" NAME="RUSER"   VALUE="$ONCPDP">\n#;
            print qq#<INPUT TYPE="hidden" NAME="RPASS"   VALUE="$ONPIs{$ONCPDP}">\n#;

            print qq#<INPUT TYPE="Submit" NAME="Submit" VALUE="Select">\n#;
            print qq#</FORM>\n#;
            print qq#</td>#;
            print "<td width=150>$OPharmacy_Name</td>\n";
            print "<td>$ONCPDP</td>\n";
            print "<td>$ONPIs{$ONCPDP}</td>\n";
            print "<td>$Pharmacy_Business_Phones{$ONCPDP}</td>\n";
            print "<td>$Pharmacy_Addresses{$ONCPDP}<br>$Pharmacy_Citys{$ONCPDP}, $Pharmacy_States{$ONCPDP} $Pharmacy_Zips{$ONCPDP}</td>\n";
            print "</tr>\n";
            print qq#<!--end pharmacy to select-->\n#;
         }
         print "</tbody>";
         print "</table>\n";

      }
   }

   #print qq#</div>\n#;
   #print qq#<!-- end  textarea2 --> \n#;

   print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

sub process_notifications {

   my ($ENV) = &What_Env_am_I_in;
   print "ENV: $ENV<br>\n" if ($debug);

   @dirnames = ( "Emergency", "Page_1_Notifications" );

   foreach $dirname (@dirnames) {
      
      if ( $ENV =~ /DEV/i ) {
         $dskpath = "\\\\pasrv2\\WWW\\www.recon-rx.com\\Webshare\\$dirname";
      } else {
         $dskpath = "\\\\pasrv3\\WWW\\www.recon-rx.com\\Webshare\\$dirname";
      }

      my @infiles;
   
      if ( -d "$dskpath" ) {
         opendir(DIR, "$dskpath") or warn "can't open dir: $dskpath:<br>$!<br>";
         while (defined($file = readdir(DIR))) {
             $fullfilename = "$dskpath/$file";
             if ( -d "$fullfilename" || $file =~ /^\./ || $file =~ /.swp$|~$/i || $file =~ /YYYY/i ) {
                print qq#Skip file: $file<br>\n# if ($debug);
             } else {
                if ( $file !~ /Filename format/i ) {
                   print qq#do something with "$dskpath\\$file"<br>\n# if ($debug);
                   push(@infiles, "$dskpath\\$file");
                }
             }
         }
         closedir(DIR);
      }
    
      foreach $filename (sort @infiles) {
   
         if ( -e "$filename" ) {
		   if ($fullfilename =~ /emergency/i) {
             print qq#<div class="notification emergency">\n#;
		   } else {
		     print qq#<div class="notification">\n#;
		   }
           my $cnt = 0;
           open (FILE, "< $filename") || warn "Couldn't open file Emergency.txt.<br>\n$!<br>\n";
           while (<FILE>) {
              chomp;
              my $line = $_;
              $line = $nbsp if ( $line =~ /^\s*$/ );
              $cnt++;
              if ( $cnt == 1 ) {
                 if ( $dirname =~ /Emergency/i ) {
                    $title = "Emergency Notification";
                 } elsif ( $dirname =~ /Page_1/i ) {
                    $title = "Notification";
                 }
                 print qq#<H2>$title:</H2>\n#;
                 print qq#<P>\n#;
              }
              print qq#$line<br>\n#;
           }
           print qq#</P>\n# if ($cnt >= 1);
           print qq#</div>\n#;
           close(FILE);
         }
      }
   }
}

#______________________________________________________________________________

sub dropdown {

  my ($dbvar, $label, @OPTS) = @_;

  $dbvarval = $$dbvar;
  $formname = "$dbvar";
  print "sub dropdown: dbvar: $dbvar, label: $label, dbvarval: $dbvarval<br>\n" if ($verbose);

  my $foundmatch = 0;

  print qq#  <tr>\n#;
  print qq#  <th class="green" align=left>$label</th>\n#;
  print qq#  <td>\n#;
  print qq#    <SELECT NAME="$formname">\n#;
  foreach $OPT (@OPTS) {
    if ( $dbvarval =~ /^$OPT/i ) {
       $SEL = "SELECTED";
       $foundmatch++;
    } else {
       $SEL = "";
    }
    print qq#      <OPTION $SEL VALUE="$OPT">$OPT</OPTION>\n#;
  }
print "foundmatch: $foundmatch<br>\n";
  if ( $foundmatch <= 0 ) {
    $OPT = "--";
    print qq#      <OPTION SELECTED VALUE="$OPT">$OPT</OPTION>\n#;
  }
  print qq#    </SELECT>\n#;
  print qq#  </td></tr>\n#;

  print "sub dropdown: Exit. dbvar: $dbvar<br>\n" if ($verbose);
}
 
#______________________________________________________________________________
 
sub displayPharmacyRight {

  my ($jNCPDP, $jNPI) = @_;
  print qq#<!-- displayPharmacyRight -->\n#;
  print "sub displayPharmacyRight: Entry. jNCPDP: $jNCPDP, jNPI: $jNPI<br>\n" if ($debug);

# connect to the pharmacy MySQL database
# print "PHDBNAME: $PHDBNAME, dbuser: $dbuser\n" if ($debug);
 
  my $dbin     = "PHDBNAME";
  my $db       = $dbin;
  my $DBNAME   = $DBNAMES{"$dbin"};
  my $TABLE    = $DBTABN{"$dbin"};
  my $FIELDS   = $DBFLDS{"$dbin"};
  my $FIELDS2  = $DBFLDS{"$dbin"} . "2";
  my $fieldcnt = $#${FIELDS2} + 2;

  $dbp = DBI->connect("DBI:mysql:$PHDBNAME:$DBHOST",$dbuser,$dbpwd,
	     { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

  DBI->trace(1) if ($dbitrace);

  my $sql = "SELECT $PHFIELDS FROM $DBNAME.$TABLE WHERE NPI = '$jNPI'";

  $sthp = $dbp->prepare($sql);
  $sthp->execute();
  my $numofrows = $sthp->rows;
  print "Number of rows found: " . $sthp->rows . "<br>\n" if ($debug);

  @$FIELDS3 = @$FIELDS2;
  while (my @row = $sthp->fetchrow_array()) {
   (@$FIELDS3) =  @row;
   $ptr = -1;
     foreach $pc (@$FIELDS3) {
     $ptr++;
     my $name = @$FIELDS2[$ptr];
#    ${$name} = $pc || $nbsp;
	 ${$name} = $pc || "Unknown";
#    print "name: $name, value: $$name<br>\n" ;# if ($verbose);
     }
  }

  $sthp->finish();

# Close the Databases
  $dbp->disconnect;

  if ( $jNCPDP || $jNPI ) {
# Now display the page of Pharmacy information

  $DEA                   = "Unknown" if ( !$DEA );
  $DEA_Expiration        = "Unknown" if ( !$DEA_Expiration );
  $Recon_Contact_Name    = "Unknown" if ( !$Recon_Contact_Name );
  $Recon_Contact_Email   = "Unknown" if ( !$Recon_Contact_Email );
  $PIC_Contact_Name      = "Unknown" if ( !$PIC_Contact_Name );
  $PIC_Contact_Email     = "Unknown" if ( !$PIC_Contact_Email );
  $State_Permit_Number   = "Unknown" if ( !$State_Permit_Number );
  $State_Permit_Expiration_Date = "Unknown" if ( !$State_Permit_Expiration_Date || $State_Permit_Expiration_Date =~ /^\s*$|nbsp/i );

  if ( !$EOY_Report_Date || $EOY_Report_Date =~ /^\s*$|nbsp/i ) {
	$EOY_Report_Date = "Unknown";
  } else {
	my @pcs = split("-", $EOY_Report_Date);
#   $EOY_Report_Date = $pcs[1] . "/" . $pcs[2] . "/" . $pcs[0];
	$EOY_Report_Date = $pcs[1] . "/" . $pcs[2];
  }

  ### Graphs ###

  print qq#
  <!-- Required File Includes -->
  <script src="http://code.jquery.com/jquery-1.11.0.min.js"></script>
  <script src="http://code.highcharts.com/highcharts.js"></script>
  <script src="http://code.highcharts.com/modules/exporting.js"></script>
  #;
 

  $dbg = DBI->connect("DBI:mysql:$PHDBNAME:$DBHOST",$dbuser,$dbpwd,
		 { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
		
		
  $Total   = 0;
  $F1to44  = 0;
  $F45to59 = 0;
  $F60to89 = 0;
  $Fover90 = 0;

  $sql = qq#
  SELECT Total, IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90 
  FROM (
  SELECT dbNCPDPNumber, sum(dbTotalAmountPaid) Total FROM ReconRxDB.incomingtb 
  WHERE 
  dbTotalAmountPaid != -20000 && 
  dbNCPDPNumber = $NCPDP && dbBinParent != -1
  GROUP BY dbNCPDPNumber 
  ) totals 
  
  LEFT JOIN (
  SELECT dbNCPDPNumber, sum(dbTotalAmountPaid) 1to44 FROM ReconRxDB.incomingtb 
  WHERE 
  dbTotalAmountPaid != -20000 && 
  dbNCPDPNumber = $NCPDP && dbBinParent != -1 && 
  (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) && DATE(dbDateTransmitted) <= CURDATE())
  GROUP BY dbNCPDPNumber
  ) set_1to44
  ON set_1to44.dbNCPDPNumber = totals.dbNCPDPNumber 
  
  LEFT JOIN (
  SELECT dbNCPDPNumber, sum(dbTotalAmountPaid) 45to59 FROM ReconRxDB.incomingtb 
  WHERE 
  dbTotalAmountPaid != -20000 && 
  dbNCPDPNumber = $NCPDP && dbBinParent != -1 && 
  (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
  GROUP BY dbNCPDPNumber
  ) set_45to59
  ON set_45to59.dbNCPDPNumber = totals.dbNCPDPNumber
  
  LEFT JOIN (
  SELECT dbNCPDPNumber, sum(dbTotalAmountPaid) 60to89 FROM ReconRxDB.incomingtb 
  WHERE 
  dbTotalAmountPaid != -20000 && 
  dbNCPDPNumber = $NCPDP && dbBinParent != -1 && 
  (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
  GROUP BY dbNCPDPNumber
  ) set_60to89
  ON set_60to89.dbNCPDPNumber = totals.dbNCPDPNumber
  
  LEFT JOIN (
  SELECT dbNCPDPNumber, sum(dbTotalAmountPaid) over90 FROM ReconRxDB.incomingtb 
  WHERE 
  dbTotalAmountPaid != -20000 && 
  dbNCPDPNumber = $NCPDP && dbBinParent != -1 && 
  (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
  GROUP BY dbNCPDPNumber
  ) set_over90 
  ON set_over90.dbNCPDPNumber = totals.dbNCPDPNumber
  #;

  print "<pre>sql:<br>$sql<br></pre>\n" if ($debug);

  $sthg = $dbg->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  while (my @row = $sthg->fetchrow_array()) {
	($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90) = @row;
	print qq#($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90)\n# if ($debug);
  }
  $sthg->finish();

  $All_Aging   = &commify(sprintf("%0.2f", $All_Aging));
  $F1to44  = &commify(sprintf("%0.2f", $F1to44));
  $F45to59 = &commify(sprintf("%0.2f", $F45to59));
  $F60to89 = &commify(sprintf("%0.2f", $F60to89));
  $Fover90 = &commify(sprintf("%0.2f", $Fover90));
  
  $all_payments_pie = 0;
  $all_payments_bar = 0;

  ### Pie Chart Data ############################################################
  my $piedata = "";
  my $sql = "
  SELECT R_TPP_PRI, Third_Party_Payer_Name, sum(R_BPR02_Check_Amount) as Amount
  FROM (	
    SELECT 
    date_format(R_CheckReceived_Date, '%Y-%m') as MonthRec, 
    R_TPP_PRI, R_BPR02_Check_Amount
    FROM (
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
      FROM reconrxdb.835remitstb
        WHERE 
        R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
      UNION 
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
      FROM reconrxdb.835remitstb_archive 
        WHERE 
        R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
    ) all_rec_remits
    GROUP BY R_TRN02_Check_Number
    ORDER BY MonthRec, R_BPR02_Check_Amount DESC
  ) monthgroups
  LEFT JOIN officedb.third_party_payers 
  ON R_TPP_PRI = Third_Party_Payer_ID
  GROUP BY R_TPP_PRI
  ORDER BY Amount DESC
  LIMIT 8
  ;";

  $sthg = $dbg->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  while (my @row = $sthg->fetchrow_array()) {
    ($dbkey, $tpp, $total) =  @row;
    #print "<p>$tpp - $total</p>";
    $piedata .= "['${tpp}', ${total}],";
    $all_payments_pie += $total;
  }
  $sthg->finish();
 
 
  my $sql = "
  SELECT R_TPP_PRI, Third_Party_Payer_Name, sum(Count) as Count, sum(Total) as Total 
  FROM (
    SELECT '000000' as R_TPP_PRI, 'Other' as Third_Party_Payer_Name, COUNT(R_TPP_PRI) as Count, sum(R_BPR02_Check_Amount) as Total
    FROM ( 
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount 
      FROM reconrxdb.835remitstb 
        WHERE 
        R_TS3_NCPDP = $jNCPDP
        && R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        GROUP BY R_TRN02_Check_Number
      UNION 
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount 
      FROM reconrxdb.835remitstb_archive
        WHERE 
        R_TS3_NCPDP = $jNCPDP
        && R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        GROUP BY R_TRN02_Check_Number
    ) all_remits
    LEFT JOIN officedb.third_party_payers 
    ON R_TPP_PRI = Third_Party_Payer_ID
    GROUP BY R_TPP_PRI DESC 
    ORDER BY Total DESC
    LIMIT 8, 999999
  ) other
  ;";

  $sthg = $dbg->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  while (my @row = $sthg->fetchrow_array()) {
    my ($dbkey_other, $tpp_other, $count_other, $total_other) =  @row;
    #print "<p>$tpp_other - $total_other</p>";
	#if ($tpp_other =~ //) { $tpp_other = 'Other'; }
	#if ($total_other =~ //) { $total_other = 0; } 
	if ($total_other !~ //) {
      $piedata .= "['${tpp_other}', ${total_other}]";
	  $all_payments_pie += $total_other;
	}
  }
  $sthg->finish();
  ###############################################################################
 
  ### Bar Chart Data ############################################################
 
  my $sql = "
  SELECT MonthRec, sum(R_BPR02_Check_Amount) as Amount 
  FROM (	
    SELECT 
    date_format(R_CheckReceived_Date, '%Y-%m') as MonthRec, 
    R_TPP_PRI, R_BPR02_Check_Amount
    FROM (
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
      FROM reconrxdb.835remitstb
        WHERE 
        R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
      UNION 
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
      FROM reconrxdb.835remitstb_archive 
        WHERE 
        R_CheckReceived_Date IS NOT NULL
        && date_format(R_CheckReceived_Date, '%Y-%m') >= date_format((CURDATE() - INTERVAL 5 MONTH), '%Y-%m')
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
    ) all_rec_remits
    GROUP BY R_TRN02_Check_Number
    ORDER BY MonthRec, R_BPR02_Check_Amount DESC
  ) monthgroups
  GROUP BY MonthRec
  ";

  $sthg = $dbg->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;
 
  my @monthsrec = ();
 
  my $dataset_curyear = "";
  while (my @row = $sthg->fetchrow_array()) {
	my ($monthrec, $amountrec, $countrec) =  @row;   
    $dataset_curyear .= "$amountrec, ";
    push(@monthsrec, $monthrec); 
	$all_payments_bar += $amountrec;
  }
  $dataset_curyear =~ s/,+$//;
  $sthg->finish();
 
 
  my $dataset_lastyear = "";
  my $categories = "";
 
  foreach (@monthsrec) { 
    my $yearmonth = $_;
   
    #split up year and month
    my ($year, $month) = split('-', $yearmonth);
   
    #build categories for x axis
    $categories .= qq#'$month-$year', #;
   
    #subtract a year
    $year = $year - 1;
    $yearmonth = "$year-$month";
   
   
    my $sql = "
    SELECT MonthRec, sum(R_BPR02_Check_Amount) as Amount 
    FROM (	
    SELECT 
    date_format(R_CheckReceived_Date, '%Y-%m') as MonthRec, 
    R_TPP_PRI, R_BPR02_Check_Amount
      FROM (
        SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
		FROM reconrxdb.835remitstb
        WHERE date_format(R_CheckReceived_Date, '%Y-%m') = '$yearmonth'
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
      UNION 
      SELECT R_TPP_PRI, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_CheckReceived_Date 
	  FROM reconrxdb.835remitstb_archive 
        WHERE date_format(R_CheckReceived_Date, '%Y-%m') = '$yearmonth'
        && R_TS3_NCPDP = $jNCPDP
        GROUP BY R_TRN02_Check_Number
      ) all_rec_remits
      GROUP BY R_TRN02_Check_Number
      ORDER BY MonthRec, R_BPR02_Check_Amount DESC
    ) monthgroups
    GROUP BY MonthRec
    ";
   
    #print "<pre>$sql</pre><br /><br />";
 
	$sthg = $dbg->prepare($sql);
	$sthg->execute();
    my $numofrows = $sthg->rows;
 
    if ($numofrows > 0) {
      while (my @row = $sthg->fetchrow_array()) {
	    my ($monthrec, $amountrec, $countrec) =  @row;  
        #if ($amountrec =~ // ) { $amountrec = 0; }
        #print $monthrec.'<br />';
        $dataset_lastyear .= "$amountrec, ";
      }
    } else {
      $dataset_lastyear .= "0, ";
    }
    $sthg->finish();
  }
 
  $dataset_lastyear =~ s/,+$//;
  
  #print qq#<p>Pie Chart Total: $all_payments_pie || Bar Chart Total: $all_payments_bar</p>#;
 
 
###############################################################################

  $dbg->disconnect;
  
###############################################################################  
 
  if ($All_Aging > 0 && $all_payments_pie > 0 && $all_payments_bar > 0) {
    # Print Pie Chart
    print qq#
    <script>
    \$(function () {
      \$('\#container').highcharts({
        chart: {
          plotBackgroundColor: null,
          plotBorderWidth: null,
          plotShadow: false,
          margin: [30, 0, 0, 0]
        },
        title: {
          text: 'Payment to Pharmacy (past 6 months)'
        },
        tooltip: {
          pointFormat: '\$<b>{point.y:,.2f}</b> ({point.percentage:.1f}%)'
        },
        credits: {
          enabled: false
        }, 
        plotOptions: {
          pie: {
            allowPointSelect: true,
            cursor: 'pointer',
            dataLabels: {
              enabled: true,
              color: '\#000000',
              connectorColor: '\#000000',
              format: '<b>{point.name}</b>: {point.percentage:.1f}%'
            }
          }
        },
        series: [{
          type: 'pie',
          name: 'data',
          data: [ $piedata ]
        }]
      });
    });
    
    \$(function () {
      \$('\#container2').highcharts({
        chart: {
          type: 'column'
        },
        title: {
          text: 'Dollars Reconciled (by month)'
        },
        subtitle: {
          text: 'Year to year comparison, where data is available'
        },
		credits: {
			enabled: false
		}, 
        xAxis: {
          categories: [ $categories ]
        },
        yAxis: {
          min: 0,
          title: {
            text: 'dollars'
          }
        },
        tooltip: {
          headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
          pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
                       '<td style="padding:0,0,0,3px; text-align: right;">\$<b>{point.y:,.2f}</b></td></tr>',
          footerFormat: '</table>',
          shared: true,
          useHTML: true
        },
        plotOptions: {
          column: {
            pointPadding: 0.2,
            borderWidth: 0
          }
        },
        series: [{
          name: 'Displayed Date',
          data: [ $dataset_curyear ]
        }, {
          name: 'Previous Year',
          data: [ $dataset_lastyear ]
        }]
      });
    });
    </script>
    #;
     
    ### Display Charts and Current Aging
    print qq#
    <div style="position: relative;">
    <div id="container" style="position: relative; float: left; width: 600px; height: 250px; margin: 0 auto;"></div>
    <div class="dashboard_aging">
    <h2>Current Aging</h2>
    <!--
    <div class="dashboard_aging_category">
      <div class="dashboard_aging_value">\$$Total</div>
      <div class="dashboard_aging_header">Total</div>
    </div>
    -->
    <div class="dashboard_aging_category">
      <div class="dashboard_aging_value value1">\$$F1to44</div>
      <div class="dashboard_aging_header">1 to 44 days</div>
    </div>
    <div class="dashboard_aging_category">
      <div class="dashboard_aging_value value2">\$$F45to59</div>
      <div class="dashboard_aging_header">45 to 59 days</div>
    </div>
    <div class="dashboard_aging_category">
      <div class="dashboard_aging_value value3">\$$F60to89</div>
      <div class="dashboard_aging_header">60 to 90 days</div>
    </div>
    <div class="dashboard_aging_category">
      <div class="dashboard_aging_value value4">\$$Fover90</div>
      <div class="dashboard_aging_header">Over 90 days</div>
    </div>
    </div>
    </div>
    <div style="clear: both;"></div>
    <hr style="margin: 18px 0px; color: \#DDD;" />
    <div id="container2" style="min-width: 200px; height: 400px; margin: 0 auto;"></div>
    <hr style="margin: 18px 0px; color: \#DDD;" />
    #;
  } else {
  
  ### Show this to new stores with no data feed setup yet.
  
  print qq#<h1 class="page_title">Welcome to ReconRx!</h1>#;
  
  print qq#
  <p class="notification">
  We're currently working on setting up your data feed. Once established, your ReconRx Dashboard will display on this page. Thank you for working with us!
  </p>#;
  
  }
  
  # print qq#
  # <div style="position: relative; width: 100%">
  # <div class="column_full">
    # <div class="column_full_box">
      # <div class="demo_title">My Pharmacy Success Stories</div>
      # <div class="demo_value">\$0.00</div>
    # </div>
    # <div class="column_full_box">
      # <div class="demo_title">Program Success Stories</div>
      # <div class="demo_value">\$0.00</div>
    # </div>
    # <div class="column_full_box">
      # <div class="demo_title">Payments Received at Pharmacy, over the past 30 days</div>
      # <div class="demo_value">\$0.00</div>
    # </div>
    # <div class="column_full_box">
      # <div class="demo_title">Open Claims aged over 60 days</div>
      # <div class="demo_value">\$0.00</div>
    # </div>
  # </div>
  # </div>
  
  # <div style="clear: both;"></div>
  # <br /><br />
  ;
  
  print qq#
  <div style="position: relative; width: 100%">
  <div class="column">
    <div class="column_box">
      <div class="demo_title">Phone</div>
      <div class="demo_value">$Business_Phone</div>
    </div>
    <div class="column_box">
      <div class="demo_title">Fax</div>
      <div class="demo_value">$Fax_Number</div>
    </div>
    <div class="column_box">
      <div class="demo_title">Contact</div>
      <div class="demo_value">$Recon_Contact_Name</div>
    </div>
    <div class="column_box">
      <div class="demo_title">Email</div>
      <div class="demo_value">$Recon_Contact_Email</div>
    </div>
  </div>
  <div class="column">
    <div class="column_box">
      <div class="demo_title">NCPDP</div>
      <div class="demo_value">$NCPDP</div>
    </div>
    <div class="column_box">
      <div class="demo_title">NPI</div>
      <div class="demo_value">$NPI</div>
    </div>
    <div class="column_box">
      <div class="demo_title">Fiscal EOY</div>
      <div class="demo_value">$EOY_Report_Date</div>
    </div>
  </div>
  </div>
  
  <div style="clear: both;"></div>
  <br />
  
  <p style="float: right; font-size: 12px; padding: 0 20px 0 0;">*This page is updated once daily</p>
  #;

    if ( $WHICHDB =~ /^Webinar$/i ) {
      #&Print_Canned_At_a_Glance;
    } else {
      #&Print_Once_Daily_At_a_Glance;
    }
 
  }

  print "sub displayPharmacyRight: Exit.<br>\n" if ($debug);
}
   
#______________________________________________________________________________
   
sub Print_Canned_At_a_Glance {

  print "sub Print_Canned_At_a_Glance. Entry. WHICHDB: $WHICHDB<br>\n" if ($debug);

  my $FILE = "At_a_Glance_Canned";
  my ($message, @array) = &read_canned_file($FILE);
  foreach $line (@array) {
	print "$line\n";
  }

  print "sub Print_Canned_At_a_Glance. Exit<br>\n" if ($debug);

}

#______________________________________________________________________________

sub Print_Once_Daily_At_a_Glance {

 print "sub Print_Once_Daily_At_a_Glance. Entry. WHICHDB: $WHICHDB<br>\n" if ($debug);

  my $infile = substr("0000000" . $RUSER, -7) . ".html";
  my $FILE = "D:\\WWW\\www.recon-rx.com\\Home_Pages\\$infile";
# my $FILE = "\\\\pasrv3\\WWW\\www.recon-rx.com\\Home_Pages\\$infile";
# print "FILE: $FILE<br>\n";
  open(FILE, "< $FILE") || warn "Couldn't open home page.<br>\n$!<br>\n<br>\n";
  print "<center>";
  while (<FILE>) {
	chomp;
	print "$_\n";
  }
  print "</center>";
  close(FILE);

  print "sub Print_Once_Daily_At_a_Glance. Exit<br>\n" if ($debug);

}

#______________________________________________________________________________

sub viewfield {
#
# if MODE = "View", just display field name and value
# if MODE = "Update", display field name and open up for edit

  my ($MODE, $screenval, $name, $color, @OPTS) = @_;
  my $NAME  = "UpDB_" . $name;
  my $value = $$name;

  $sizeopts = $#OPTS;

  if ( $MODE =~ /View/i ) {
	# View
	if ( $screenval =~ /website/i && $value !~ /^\s*NA\s*$/i ) {
	   if ( $value =~ /^http/i ) {
		  $URL = $value;
	   } else {
		  $URL = "http://" . $value;
	   }
	   # print "<tr><th>$value</th><td>$URL</td></tr>\n";
	   print qq#<tr><th class="$color" align=left>${screenval}:</th><td><a href="$URL" target=new>$value</a></td></tr>\n#;
	} else {
		print qq#<tr><th class="$color" align=left>${screenval}:</th><td>$value</td></tr>\n#;
	}
  } else {
	# Update
	if ( $sizeopts <= 0 ) {
	  if ( $NAME =~ /Comments/i ) {
		 print qq#<tr><th class="$color" align=left>${screenval}:</th><td><TEXTAREA NAME="$NAME" COLS=30 ROWS=8 WRAP="soft">$value</TEXTAREA></td></tr>\n#;
	  } else {
		 print qq#<tr><th class="$color" align=left>${screenval}:</th><td><INPUT TYPE="text" SIZE=20 NAME="$NAME" VALUE="$value"</td></tr>\n#;
	  }
	} else {
	  &dropdown( "$name", "$screenval", @OPTS);
	}
  }
}

#______________________________________________________________________________
	   