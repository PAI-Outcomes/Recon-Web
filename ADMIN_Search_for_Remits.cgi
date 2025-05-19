# Jay Herder
# Date: 06/25/2012
# Review_My_Aging.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

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

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$RUSER      = $in{'RUSER'};
$RPASS      = $in{'RPASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$payer  = $in{'payer'};
$keywords   = $in{'keywords'};
$searchfor  = $in{'searchfor'};

$OWNER      = $in{'OWNER'};
$OWNERPASS  = $in{'OWNERPASS'};

($USER)  = &StripJunk($USER);
($PASS)  = &StripJunk($PASS);
($RUSER) = &StripJunk($RUSER);
($RPASS) = &StripJunk($RPASS);
($inTPP) = &StripJunk($inTPP);
($inBIN) = &StripJunk($inBIN);
($inBINP)= &StripJunk($inBINP);

$debug++ if ( $verbose );
$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";

#______________________________________________________________________________

&readsetCookies;

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
$CHECKYEAR = $year + 1;

$RUSER = $USER if ( $RUSER =~ /^\s*$/ );

#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);

# print qq#USER: $USER, PASS: $PASS, VALID: $VALID, isMember: $isMember\n# if ($debug);

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;
   &ReconRxGotoNewLogin;

   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;

   exit(0);
}

#______________________________________________________________________________

# jlh. 08/02/2016. Don't overwrite the "ENV" variable, but use "LOCENV" for testing 
($LOCENV) = &What_Env_am_I_in;
####$LOCENV = "DONTDO";	# override to remove from development when not needed
# print "LOCENV: $LOCENV<br>\n";

print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
   print "dol0: $0<br>\n";
   print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
   print "<hr size=4 noshade color=blue>\n";
   print "PROG: $PROG<br>\n";
   print "<br>\n";
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
   my $key;
   foreach $key (sort keys %in) {
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
#  print "inNPI: $inNPI, dispNPI: $dispNPI<br>\n";
#  print "inNCPDP: $inNCPDP, dispNCPDP: $dispNCPDP<br>\n";
   print "<hr size=4 noshade color=blue>\n";
}

&readPharmacies;
&readThirdPartyPayers;

%PAYERS = ();
@PAYERS = ();

if ( $debug ) {
   print "<br>\n";
   print "<table border=1>\n";
   print "<tr><th>payer</th>     <td>$payer</td></tr>\n";
   print "<tr><th>keywords</th>  <td>$keywords</td></tr>\n";
   print "<tr><th>searchfor</th> <td>$searchfor</td></tr>\n";
   print "</table>\n";
   print "<br>\n";
}

$root = "\\\\pasrv1\\FTPShare\\home.recon-rx.com_processed";
&read_payers_from_DIR_Listing($root);

if ($payer == "") {
  $display_payer = $PAYERS[0];
} else {
  $display_payer = $payer;
}
if ($keywords  == "") {
  $display_keywords  = "BPR|TRN|CLP|PLB";
 } else {
  $display_keywords  = $keywords;
}

@jkeywords = ("Any", "BPR", "TRN", "CLP", "PLB");

print qq#<div id="wrapper">\n#;
print qq#<h1>Keyword Searching</h1>\n#;
print qq#<hr />\n#;

print qq#<form action="$PROG" method="post">\n#;
print qq#<table class="secondary">\n#;
#print qq#<tr><th colspan=2>For Extensions, use regex strings like ".txt$", ".html$", or both use ".txt$|.html$".</th></tr>\n#;

#-----
print qq#<tr><th align=left>Payer:</th>\n#;
print qq#<td align=left><SELECT name="payer">\n#;
foreach $value (sort @PAYERS) {
  $selected = "";
  if ( $value eq $PAYERS || $value == $PAYERS ) {
     $selected = "selected";
  }
  print qq#  <OPTION $selected VALUE="$value">$value</OPTION>\n#;
}
print qq#</SELECT>\n#;
print qq#</td></tr>\n#;
#-----
print qq#<tr><th align=left>Keywords:</th>\n#;
print qq#<td align=left><SELECT name="keywords"">\n#;
foreach $value (sort @jkeywords) {
  $selected = "";
  if ( $value eq $keywords || $value == $keywords ) {
     $selected = "selected";
  }
  print qq#  <OPTION $selected VALUE="$value">$value</OPTION>\n#;
}
print qq#</SELECT>\n#;
#-----

print qq#<tr><th align=left>Search for:</th>\n#;
print qq#<td align=left><input type="text" name="searchfor" value="$searchfor" class="input-text-form" style="width: 80px;">\n#;
print qq#</td></tr>\n#;

print qq#<tr><th colspan=2><INPUT class="button-form" TYPE="submit" VALUE="Search"></th></tr>\n#;
print qq#</table>\n#;
print qq#</form>\n#;
print qq#</div>\n#;

if ( $payer && $keywords && $searchfor ) {
   $payerdir = $root . "\\$payer";
#  print "using payerdir: $payerdir<hr>\n" if ($dbug);
#  print "<hr>\n";
   $grep = "C:\\MiscPrograms\\UnxUpdates\\grep";
   if ( $keywords =~ /Any/i ) {
     $cmd    = qq#"$grep" -iER "$searchfor" "$payerdir#;
     $cmdout = qq#grep -iER "$searchfor" "$payerdir#;
   } else {
     $cmd    = qq#"$grep" -iER "$keywords" "$payerdir" | "$grep" -ie "$searchfor"#;
     $cmdout = qq#grep -iER "$keywords" "$payerdir" | $grep -ie "$searchfor"#;
   }

   print "cmd:<br><font size=-1>$cmdout</font><br><hr>\n" if ($debug);

   ($cmd, $out) = &docmd($cmd);
   my @out = split("\n", $out);
   foreach $pc (sort @out) {
      $pc =~ s/\n//g;
      ($p1, $p2) = split(/:/, $pc, 2);
      if ( !$filesfound{$p1} ) {
         $p1 =~ s/\//\\/g;
         $filesfound{$p1}++;
         (my $newp1 = $p1) =~ s/\\/\//g;
         my $webpath = "file:///" . $newp1;
#        print qq#<hr><strong>FILE:<br><a href="$webpath" target="_Blank">$p1</a></strong><br>#;
         print qq#<hr><strong><font size=-1>FILE:<br>$p1</font></strong><br>#;
      }
      print "$p2<br>";
   }
}


#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub read_payers_from_DIR_Listing { 

  my ($root) = @_;
  my $debug = 0;

  opendir my $dh, "$root" or die "$0: opendir: $!";

  my @dirs = grep {-d "$root/$_" && ! /^\.{1,2}$/} readdir($dh);

  $ptr = 0;
  foreach $subdir (sort @dirs) {
    next if ( $subdir =~ /_JWORK_|processed$|Switch$/i );
    printf "%3d) subdir: %s<br>\n", $ptr, $subdir if ($debug);
    $PAYERS{$subdir}++;
    push(@PAYERS, $subdir);
    $ptr++;
  }
  
  close $dh;

}

#______________________________________________________________________________
